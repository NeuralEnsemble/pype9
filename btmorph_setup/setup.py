#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="btmorph",
    version="0.1dev",
    package_data={'btmorph': ['btmorph']},
    packages = find_packages(),
    author="B.Torben-Nielsen",
    # add your name here if you contribute to the code
    author_email="",
    description="",
    long_description=open("readme.rst").read(),
    license="The MIT License (MIT)",
    keywords="morphology, swc",
    url="",
    classifiers=['Development Status :: ',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: MIT',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Topic :: Scientific/Engineering'],
    install_requires=[],
    #cannot add the the requirements btmorph, and nineml above, because if those install requirements are listed 
    #Then this install script searches pip for those packages. btmorph is not a pip package, and it is not desirable to overwrite specific development versions 
    #of nineml with the pip stable version.
    tests_require=['nose']
)
