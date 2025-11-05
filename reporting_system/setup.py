#!/usr/bin/env python3
"""
Setup script for the Reporting System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="comprehensive-reporting-system",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@company.com",
    description="Comprehensive reporting and visualization system with automated report generation, interactive dashboards, and multi-format exports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/reporting-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Financial :: Spreadsheet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.4.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'reporting-system=reporting_system.main:cli',
            'reporting-dashboard=reporting_system.main:dashboard',
            'reporting-scheduler=reporting_system.main:start_scheduler',
        ],
    },
    include_package_data=True,
    package_data={
        'reporting_system': [
            'templates/*.html',
            'config/*.yaml',
            'assets/*',
        ],
    },
    keywords="reporting dashboard visualization automation pdf html excel scheduled-reports",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/reporting-system/issues",
        "Source": "https://github.com/yourusername/reporting-system",
        "Documentation": "https://reporting-system.readthedocs.io/",
    },
)