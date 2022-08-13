from __future__ import print_function

import pipes
import shutil
import subprocess
import sys
import traceback
from logging import StreamHandler, getLogger
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.sdist import sdist


if sys.platform == "win32":
    from subprocess import list2cmdline
else:

    def list2cmdline(cmd_list):
        return " ".join(map(pipes.quote, cmd_list))


log = getLogger()
log.addHandler(StreamHandler(sys.stdout))


# -----------------------------------------------------------------------------
# Basic Constants
# -----------------------------------------------------------------------------


# the name of the project
NAME = "idom"

# basic paths used to gather files
ROOT_DIR = Path(__file__).parent
SRC_DIR = ROOT_DIR / "src"
PKG_DIR = SRC_DIR / NAME
JS_DIR = SRC_DIR / "client"


# -----------------------------------------------------------------------------
# Package Definition
# -----------------------------------------------------------------------------


package = {
    "name": NAME,
    "python_requires": ">=3.7",
    "packages": find_packages(str(SRC_DIR)),
    "package_dir": {"": "src"},
    "description": "It's React, but in Python",
    "author": "Ryan Morshead",
    "author_email": "ryan.morshead@gmail.com",
    "url": "https://github.com/rmorshea/idom",
    "license": "MIT",
    "platforms": "Linux, Mac OS X, Windows",
    "keywords": ["interactive", "widgets", "DOM", "React"],
    "include_package_data": True,
    "zip_safe": False,
    "classifiers": [
        "Environment :: Web Environment",
        "Framework :: AsyncIO",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: Software Development :: Widget Sets",
        "Typing :: Typed",
    ],
}


# -----------------------------------------------------------------------------
# Library Version
# -----------------------------------------------------------------------------

pkg_root_init_file = PKG_DIR / "__init__.py"
for line in pkg_root_init_file.read_text().split("\n"):
    if line.startswith('__version__ = "') and line.endswith('"  # DO NOT MODIFY'):
        package["version"] = (
            line
            # get assignment value
            .split("=", 1)[1]
            # remove "DO NOT MODIFY" comment
            .split("#", 1)[0]
            # clean up leading/trailing space
            .strip()
            # remove the quotes
            [1:-1]
        )
        break
else:
    print(f"No version found in {pkg_root_init_file}")
    sys.exit(1)


# -----------------------------------------------------------------------------
# Requirements
# -----------------------------------------------------------------------------


requirements = []
with (ROOT_DIR / "requirements" / "pkg-deps.txt").open() as f:
    for line in map(str.strip, f):
        if not line.startswith("#"):
            requirements.append(line)
package["install_requires"] = requirements

_current_extras = []
extra_requirements = {"all": []}  # type: ignore
extra_requirements_path = ROOT_DIR / "requirements" / "pkg-extras.txt"
with extra_requirements_path.open() as f:
    for line in map(str.strip, f):
        if line.startswith("#") and line[1:].strip().startswith("extra="):
            _current_extras = [e.strip() for e in line.split("=", 1)[1].split(",")]
            if "all" in _current_extras:
                raise ValueError("%r uses the reserved extra name 'all'")
            for e in _current_extras:
                extra_requirements[e] = []
        elif _current_extras:
            for e in _current_extras:
                extra_requirements[e].append(line)
            extra_requirements["all"].append(line)
        elif line:
            raise ValueError(
                f"No '# extra=<name>' header before requirements in {extra_requirements_path}"
            )
package["extras_require"] = extra_requirements


# -----------------------------------------------------------------------------
# Library Description
# -----------------------------------------------------------------------------


with (ROOT_DIR / "README.md").open() as f:
    long_description = f.read()

package["long_description"] = long_description
package["long_description_content_type"] = "text/markdown"


# ----------------------------------------------------------------------------
# Build Javascript
# ----------------------------------------------------------------------------


def build_javascript_first(cls):
    class Command(cls):
        def run(self):
            log.info("Installing Javascript...")
            try:
                npm = shutil.which("npm")  # this is required on windows
                if npm is None:
                    raise RuntimeError("NPM is not installed.")
                for args in (f"{npm} install", f"{npm} run build"):
                    args_list = args.split()
                    log.info(f"> {list2cmdline(args_list)}")
                    subprocess.run(args_list, cwd=str(JS_DIR), check=True)
            except Exception:
                log.error("Failed to install Javascript")
                log.error(traceback.format_exc())
                raise
            else:
                log.info("Successfully installed Javascript")
            super().run()

    return Command


package["cmdclass"] = {
    "sdist": build_javascript_first(sdist),
    "develop": build_javascript_first(develop),
}

if sys.version_info < (3, 10, 6):
    from distutils.command.build import build

    package["cmdclass"]["build"] = build_javascript_first(build)
else:
    from setuptools.command.build_py import build_py

    package["cmdclass"]["build_py"] = build_javascript_first(build_py)


# -----------------------------------------------------------------------------
# Install It
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    setup(**package)
