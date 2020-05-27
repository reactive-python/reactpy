from __future__ import print_function

from setuptools import setup, find_packages
from distutils.command.build import build  # type: ignore
from distutils.command.sdist import sdist  # type: ignore
from setuptools.command.develop import develop
import os
import subprocess

# the name of the project
name = "idom"

# basic paths used to gather files
here = os.path.abspath(os.path.dirname(__file__))
root = os.path.join(here, name)


# -----------------------------------------------------------------------------
# Package Definition
# -----------------------------------------------------------------------------


package = {
    "name": name,
    "python_requires": ">=3.6",
    "packages": find_packages(exclude=["tests*"]),
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
with open(os.path.join(here, "requirements", "prod.txt"), "r") as f:
    for line in map(str.strip, f):
        if not line.startswith("#"):
            requirements.append(line)
package["install_requires"] = requirements

_current_extras = []
extra_requirements = {"all": []}  # type: ignore
extra_requirements_path = os.path.join(here, "requirements", "extras.txt")
with open(extra_requirements_path, "r") as f:
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
            msg = "No '# extra=<name>' header before requirements in %r"
            raise ValueError(msg % extra_requirements_path)
package["extras_require"] = extra_requirements


# -----------------------------------------------------------------------------
# Library Description
# -----------------------------------------------------------------------------


with open(os.path.join(here, "README.md")) as f:
    long_description = f.read()

package["long_description"] = long_description
package["long_description_content_type"] = "text/markdown"


# ----------------------------------------------------------------------------
# Build Javascript
# ----------------------------------------------------------------------------


def build_javascript_first(cls):
    class Command(cls):
        def run(self):
            command = ["sh", os.path.join(here, "scripts", "build.sh")]
            subprocess.check_call(command, cwd=here)
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
