#!/usr/bin/env python3
"""
Setup script for Multi-Objective Optimization Platform
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="moo-gui-platform",
    version="1.0.0",
    author="Kushagra Rajput",
    author_email="rajputkushagra26@gmail.com",
    description="Interactive web platform for multi-objective optimization using Dash and Pymoo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kushagra0526/moo-gui-platform",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "moo-gui=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gui": ["assets/*"],
    },
    keywords="multi-objective optimization, evolutionary algorithms, pymoo, dash, plotly, NSGA-II, NSGA-III, MOEA/D",
    project_urls={
        "Source": "https://github.com/kushagra0526/moo-gui-platform",
        "Tracker": "https://github.com/kushagra0526/moo-gui-platform/issues",
    },
)