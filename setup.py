#!/usr/bin/env python3
"""Setup script for zwalker package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="zwalker",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automated walkthrough generator for Z-machine interactive fiction games",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/zwalker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies - none required for basic functionality
    ],
    extras_require={
        "ai": [
            "anthropic>=0.7.0",  # For Claude AI
            "openai>=1.0.0",     # For GPT AI
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "zwalker=zwalker.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
