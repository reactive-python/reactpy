from __future__ import print_function

from setuptools import setup, find_packages
from distutils.command.build import build  # type: ignore
from distutils.command.sdist import sdist  # type: ignore
from setuptools.command.develop import develop
import os
import sys
import subprocess

# the name of the project
name = "idom"

# basic paths used to gather files
here = os.path.abspath(os.path.dirname(__file__))
root = os.path.join(here, "src", name)


# -----------------------------------------------------------------------------
# Package Definition
# -----------------------------------------------------------------------------


package = {
    "name": name,
    "python_requires": ">=3.6,<4.0",
    "packages": find_packages("src", exclude=["tests*"]),
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
}


# -----------------------------------------------------------------------------
# requirements
# -----------------------------------------------------------------------------


requirements = []
with open(os.path.join(here, "requirements", "prod.txt"), "r") as f:
    for line in map(str.strip, f):
        if not line.startswith("#"):
            requirements.append(line)
package["install_requires"] = requirements

_current_extra_section = None
extra_requirements = {"all": []}  # type: ignore
extra_requirements_path = os.path.join(here, "requirements", "extras.txt")
with open(extra_requirements_path, "r") as f:
    for line in map(str.strip, f):
        if line.startswith("#") and line[1:].strip().startswith("extra="):
            _current_extra_section = line.split("=", 1)[1]
            if _current_extra_section == "all":
                raise ValueError("%r uses the reserved extra name 'all'")
            extra_requirements[_current_extra_section] = []
        elif _current_extra_section is not None:
            extra_requirements[_current_extra_section].append(line)
            extra_requirements["all"].append(line)
        elif line:
            msg = "No '# extra=<name>' header before requirements in %r"
            raise ValueError(msg % extra_requirements_path)
package["extras_require"] = extra_requirements


# -----------------------------------------------------------------------------
# Library Version
# -----------------------------------------------------------------------------


with open(os.path.join(root, "__init__.py")) as f:
    for line in f.read().split("\n"):
        if line.startswith("__version__ = "):
            version = eval(line.split("=", 1)[1])
            break
    else:
        print("No version found in __init__.py")
        sys.exit(1)
package["version"] = version


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
