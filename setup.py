#!/usr/bin/env python

import sys

sys.path[:0] = ["./"]

from pvData import PACKAGE_NAME

from setuptools import setup

setup(
    name=PACKAGE_NAME,
    version='0.1',
    description="Python PV Data Tools",
    author='Damion K. Wilson',
    include_package_data=True,
    platforms='any',

    install_requires=[
        "numpy",
        "pandas",
    ],

    packages = [
        PACKAGE_NAME,
    ],

    package_data={
        '': ['dataset/*/*.csv', 'notebooks/*.ipynb'],
    },

    entry_points = {
        'console_scripts': [
            "pv_console = {}.entrypoints:main".format(PACKAGE_NAME),
        ]
    },
)
