from __future__ import print_function

import pipes
import shutil
import subprocess
import sys
import traceback
from distutils import log
from distutils.command.build import build  # type: ignore
from distutils.command.sdist import sdist  # type: ignore
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.command.develop import develop


if sys.platform == "win32":
    from subprocess import list2cmdline
else:

    def list2cmdline(cmd_list):
        return " ".join(map(pipes.quote, cmd_list))


# the name of the project
name = "idom"

# basic paths used to gather files
root_dir = Path(__file__).parent
src_dir = root_dir / "src"
package_dir = src_dir / name


# -----------------------------------------------------------------------------
# Package Definition
# -----------------------------------------------------------------------------


package = {
    "name": name,
    "python_requires": ">=3.7",
    "packages": find_packages(str(src_dir)),
    "package_dir": {"": "src"},
    "description": "Control the web with Python",
    "author": "Ryan Morshead",
    "author_email": "ryan.morshead@gmail.com",
    "url": "https://github.com/rmorshea/idom",
    "license": "MIT",
    "platforms": "Linux, Mac OS X, Windows",
    "keywords": ["interactive", "widgets", "DOM", "React"],
    "include_package_data": True,
    "zip_safe": False,
    "setup_requires": ["setuptools_scm"],
    "use_scm_version": True,
    "classifiers": [
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Multimedia :: Graphics",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
}


# -----------------------------------------------------------------------------
# CLI Entrypoints
# -----------------------------------------------------------------------------


package["entry_points"] = {
    "console_scripts": ["idom = idom.__main__:main"],
}


# -----------------------------------------------------------------------------
# Requirements
# -----------------------------------------------------------------------------


requirements = []
with (root_dir / "requirements" / "pkg-deps.txt").open() as f:
    for line in map(str.strip, f):
        if not line.startswith("#"):
            requirements.append(line)
package["install_requires"] = requirements

_current_extras = []
extra_requirements = {"all": []}  # type: ignore
extra_requirements_path = root_dir / "requirements" / "pkg-extras.txt"
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


with (root_dir / "README.md").open() as f:
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
                js_dir = str(package_dir / "client" / "app")
                for cmd, *args in map(str.split, ["npm install", "npm run build"]):
                    which_cmd = shutil.which(cmd)
                    if which_cmd is None:
                        raise RuntimeError(
                            f"Failed to run command - {cmd!r} is not installed."
                        )
                    cmd_args = [which_cmd] + args
                    log.info(f"> {list2cmdline(cmd_args)}")
                    subprocess.check_call(cmd_args, cwd=js_dir)
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
    "build": build_javascript_first(build),
    "develop": build_javascript_first(develop),
}


# -----------------------------------------------------------------------------
# Install It
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    setup(**package)
