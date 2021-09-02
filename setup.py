#!usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


# import long description
def readme():
    with open('README.rst') as f:
        return f.read()


config = {
    "name": "pykosimcli",
    "version": "0.1",
    "description": "cli for working with kosim models",
    "long_description": readme(),
    "classifiers": ['Development Status :: 5 - Production/Stable',
                    'License :: OSI Approved :: MIT License',
                    'Programming Language :: Python :: 3.7',
                    'Topic :: Output Processing :: Hydraulics',
                    ],
    "keywords": ['KOSIM'],
    "url": "None",
    "download_url": "None",
    "author": "Brian Sweeney",
    "author_email": "sweeneybrian907@gmail.com",
    "license": "MIT",
    "install_requires": ["pandas", "numpy", "matplotlib", "xlsxwriter", "fdb"],
    "packages": ["pykosimcli"],
    "zip_safe": False,
    "include_package_data": True,  # includes data specified in the Manifest.in
    "scripts": [],
    "entry_points": {"console_scripts": "pykosimcli=pykosimcli.cli:main"},
    # "setup_requires": ["pytest-runner"],
    "test_suite": "pytest",
    "tests_require": ["pytest"]
}

setup(**config)
