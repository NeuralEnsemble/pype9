#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="9Line",
    version="0.1dev",
    package_data={'nineline': ['nineline', 'nineline/*.py', 'nineline/cells',
                               'nineline/cells/code_gen','nineline/cells/build',
                               'nineline/importer','nineline/pyNN','nineline/hpc',
                               'nineline/test','nineline/test/unittests',
                               'nineline/morphology']},
    packages = find_packages(),
    author="Thomas G. Close (tclose@oist.jp), Ivan Raikov (raikov@oist.jp)",
    # add your name here if you contribute to the code
    author_email="tclose@oist.jp, raikov@oist.jp",
    description="A NINEml software pipeLINE that reads and simulates networks of detailed neuronal models described in 9ml.",
    long_description=open("README.md").read(),
    license="The MIT License (MIT)",
    keywords="PipeLINE NINEml computational neuroscience modeling interoperability XML",
    url="",
    classifiers=['Development Status :: initial stages',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: MIT',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Topic :: Scientific/Engineering'],
    install_requires=['lxml', 'ply', 'numpy', 'quantities'],
    #cannot add the the requirements btmorph, and nineml above, because if those install requirements are listed 
    #Then this install script searches pip for those packages. btmorph is not a pip package, and it is not desirable to overwrite specific development versions 
    #of nineml with the pip stable version.
    tests_require=['nose']
)
