from __future__ import print_function

import os
import sys
from setuptools import find_packages
from distutils.core import setup

# -----------------------------------------------------------------------------
# Package
# -----------------------------------------------------------------------------

package = dict(
    name="idom",
    license="MIT",
    packages=find_packages(),
    description="Control the web with Python",
    classifiers=["Intended Audience :: Developers"],
    author="Ryan Morshead",
    author_email="ryan.morshead@gmail.com",
    url="https://github.com/rmorshea/idom",
    keywords=["web"],
    platforms="Linux, Mac OS X, Windows",
    package_data={"idom": ["py.typed"]},
)

# -----------------------------------------------------------------------------
# Basics
# -----------------------------------------------------------------------------

# paths used to gather files
here = os.path.abspath(os.path.dirname(__file__))
root = os.path.join(here, package["name"])

# -----------------------------------------------------------------------------
# Requirements
# -----------------------------------------------------------------------------

package["install_requires"] = ["sanic", "sanic_cors"]

# -----------------------------------------------------------------------------
# Library Version
# -----------------------------------------------------------------------------

with open(os.path.join(root, "__init__.py")) as f:
    for line in f.read().split("\n"):
        if line.startswith("__version__ = "):
            package["version"] = eval(line.split("=", 1)[1])
            break
    else:
        print("No version found in %s/__init__.py" % root)
        sys.exit(1)

# -----------------------------------------------------------------------------
# Library Description
# -----------------------------------------------------------------------------

package["long_description_content_type"] = "text/markdown"
with open(os.path.join(here, "README.md")) as f:
    package["long_description"] = f.read()

# -----------------------------------------------------------------------------
# Install It
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    setup(**package)
