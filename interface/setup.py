#! /usr/bin/env python

import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

data_files = []
if sys.platform.startswith("linux"):
    data_files.append(("/usr/share/applications", ["scripts/gas-uptake.desktop"]))

extra_files = []
extra_files.append(os.path.join(here, "requirements.txt"))
extra_files.append(os.path.join(here, "VERSION"))

with open(os.path.join(here, "gas_uptake", "VERSION")) as version_file:
    version = version_file.read().strip()

setup(
    name="gas_uptake",
    packages=find_packages(),
    package_data={"": extra_files},
    data_files=data_files,
    install_requires=["PySide2", "qtypes"],
    version=version,
    description="gas_uptake",
    author="Blaise Thompson",
    author_email="bthompson@chem.wisc.edu",
    license="MIT",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering",
    ],
    entry_points={"gui_scripts": ["gas-uptake=gas_uptake.__main__:main"]},
)
