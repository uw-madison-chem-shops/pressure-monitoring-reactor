#!/usr/bin/env python3

"""The setup script."""

import pathlib
from setuptools import setup, find_packages

here = pathlib.Path(__file__).parent

with open(here / "director" / "VERSION") as version_file:
    version = version_file.read().strip()


with open("README.md") as readme_file:
    readme = readme_file.read()


requirements = ["yaqd-core", "yaqc"]

extra_requirements = {"dev": ["black", "pre-commit"]}
extra_files = {"director": ["VERSION"]}

setup(
    author="Blaise Thompson",
    author_email="bthompson@chem.wisc.edu",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering",
    ],
    description="Gas uptake director.",
    entry_points={
        "console_scripts": [
            "yaqd-gas-uptake-director=director._gas_uptake_director:GasUptakeDirector.main",
        ],
    },
    install_requires=requirements,
    extras_require=extra_requirements,
    license="GNU Lesser General Public License v3 (LGPL)",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    package_data=extra_files,
    keywords="director",
    name="director",
    packages=find_packages(include=["director", "director.*"]),
    url="https://gitlab.com/yaq/director",
    version=version,
    zip_safe=False,
)
