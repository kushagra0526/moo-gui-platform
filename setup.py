#!/usr/bin/env python3
"""
Setup script for Multi-Objective Optimization GUI
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="moo-gui",
    version="1.0.0",
    author="MOO GUI Development Team",
    author_email="contact@moo-gui.org",
    description="Research-grade GUI for multi-objective optimization using pymoo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/moo-gui",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=0.5",
            "myst-parser>=0.15",
        ],
    },
    entry_points={
        "console_scripts": [
            "moo-gui=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gui": ["assets/*"],
    },
    keywords="multi-objective optimization, evolutionary algorithms, pymoo, GUI, NSGA-II, NSGA-III",
    project_urls={
        "Bug Reports": "https://github.com/your-username/moo-gui/issues",
        "Source": "https://github.com/your-username/moo-gui",
        "Documentation": "https://moo-gui.readthedocs.io/",
    },
)