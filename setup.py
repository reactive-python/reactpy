from __future__ import print_function

from distutils.core import setup
import os
from setuptools.command.develop import develop as DevelopCommand
from setuptools.command.install import install as InstallCommand
import sys
import subprocess


# the name of the project
name = "idom"

# basic paths used to gather files
here = os.path.abspath(os.path.dirname(__file__))
root = os.path.join(here, "src", "py", name)

# -----------------------------------------------------------------------------
# Python Version Check
# -----------------------------------------------------------------------------

if sys.version_info < (3, 6) or sys.version_info >= (3, 7):
    error = "ERROR: %s requires Python version 3.6." % name
    print(error, file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# requirements
# -----------------------------------------------------------------------------

requirements = ["sanic==18.12"]

# -----------------------------------------------------------------------------
# Library Version
# -----------------------------------------------------------------------------

with open(os.path.join(root, "__init__.py")) as f:
    for line in f.read().split("\n"):
        if line.startswith("__version__ = "):
            version = eval(line.split("=", 1)[1])
            break
    else:
        print("No version found in purly/__init__.py")
        sys.exit(1)

# -----------------------------------------------------------------------------
# Library Description
# -----------------------------------------------------------------------------

with open(os.path.join(here, "README.md")) as f:
    long_description = f.read()


# ----------------------------------------------------------------------------
# Build Javascript
# ----------------------------------------------------------------------------


class BuildStaticFiles:
    def run(self):
        command = ["bash", os.path.join(here, "scripts", "build.sh")]
        subprocess.check_call(command, cwd=here)
        super().run()


class CustomDevelopCommand(BuildStaticFiles, DevelopCommand):
    """Post-installation for development mode."""


class CustomInstallCommand(BuildStaticFiles, InstallCommand):
    """Post-installation for installation mode."""


# -----------------------------------------------------------------------------
# Install It
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    setup(
        name=name,
        version=version,
        packages=["idom"],
        package_dir={"": "src/py"},
        cmdclass={"install": CustomInstallCommand, "develop": CustomDevelopCommand},
        package_data={"src/py/idom": ["static/*"]},
        description="Control the web with Python",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="Ryan Morshead",
        author_email="ryan.morshead@gmail.com",
        url="https://github.com/rmorshea/idom",
        license="MIT",
        platforms="Linux, Mac OS X, Windows",
        keywords=["interactive", "widgets", "DOM", "React"],
        install_requires=requirements,
        python_requires=">=3.6,<4.0",
        classifiers=[
            "Intended Audience :: Developers",
            "Programming Language :: Python :: 3.6",
        ],
    )
