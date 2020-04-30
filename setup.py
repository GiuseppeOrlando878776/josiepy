#!/usr/bin/env python
# -*- coding: utf-8 -*-
# type: ignore

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = "josiepy"
DESCRIPTION = "A Python 2D Structured Mesher"
URL = "https://gitlab.com/josiepy"
EMAIL = "rubendibattista@gmail.com"
AUTHOR = "RdB"
REQUIRES_PYTHON = ">=3.7"
VERSION = "2.0.1-beta"

# What packages are required for this module to be executed?
REQUIRED = [
    "aenum",
    "matplotlib",
    "meshio[all]",
    "numba",
    "numpy",
    "scipy",
]

# Optional
GRAPHICS = []  # ["mayavi"]
DEV = [
    "invoke",
    "pytest==5.3.5",
    "pytest-benchmark",
    "pytest-cov",
    "pytest-flake8",
    "pytest-mock",
    "pytest-mypy",
    "pytest-xdist",
]
DOCS = [
    "invoke",
    "sphinx",
    "sphinx_rtd_theme",
    "sphinx-autodoc-typehints",
    "sphinx-markdown-tables",
    "sphinxcontrib-bibtex",
    "recommonmark",
]
EXAMPLES = ["jupyter", "ipywidgets", "ipyevents", "nbdime", "RISE"]

ALL = GRAPHICS + DEV + EXAMPLES + DOCS

# What packages are optional?
EXTRAS = {
    "all": ALL,
    "dev": DEV,
    "examples": EXAMPLES,
    "gfx": GRAPHICS,
    "docs": DOCS,
}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for
# that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, "__version__.py")) as f:
        exec(f.read(), about)
else:
    about["__version__"] = VERSION


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print("\033[1m{0}\033[0m".format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        os.system(
            "{0} setup.py sdist bdist_wheel --universal".format(sys.executable)
        )

        self.status("Uploading the package to PyPI via Twine…")
        os.system("twine upload dist/*")

        self.status("Pushing git tags…")
        os.system("git tag v{0}".format(about["__version__"]))
        os.system("git push --tags")

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(
        exclude=["tests", "*.tests", "*.tests.*", "tests.*"]
    ),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],
    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="BSD",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    # $ setup.py publish support.
    cmdclass={"upload": UploadCommand},
)
