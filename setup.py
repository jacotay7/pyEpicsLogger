#!/usr/bin/env python3
"""
Setup script for pyEpicsLogger - Multi-Channel EPICS Process Variable Logger
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pyEpicsLogger",
    version="1.0.0",
    author="Jacob Taylor",
    author_email="jtaylor@keck.hawaii.edu",
    description="A command-line tool to monitor multiple EPICS Process Variable channels and log all value changes with timestamps to CSV files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jacotay7/pyEpicsLogger",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pyepicslogger=pyEpicsLogger.epicsLogger:main",
            "epicslogger=pyEpicsLogger.epicsLogger:main",
        ],
    },
    include_package_data=True,
    package_data={
        "pyEpicsLogger": ["*.txt", "*.md"],
    },
    project_urls={
        "Bug Reports": "https://github.com/jacotay7/pyEpicsLogger/issues",
        "Source": "https://github.com/jacotay7/pyEpicsLogger",
        "Documentation": "https://github.com/jacotay7/pyEpicsLogger#readme",
    },
    keywords="epics pv monitor logger data acquisition scientific instrumentation",
    zip_safe=False,
)
