#!/usr/bin/env python

import os
import re
from setuptools import setup


def parse_requirements():
    """Rudimentary parser for the `requirements.txt` file
    We just want to separate regular packages from links to pass them to the
    `install_requires` and `dependency_links` params of the `setup()`
    function properly.
    """
    try:
        requirements = \
            map(str.strip, local_file('requirements.txt').splitlines())
    except IOError:
        raise RuntimeError("Couldn't find the `requirements.txt' file :(")

    links = []
    pkgs = []
    for req in requirements:
        if not req:
            continue
        if 'http:' in req or 'https:' in req:
            links.append(req)
            name, version = re.findall("\#egg=([^\-]+)-(.+$)", req)[0]
            pkgs.append('{0}=={1}'.format(name, version))
        else:
            pkgs.append(req)

    return pkgs, links


def local_file(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read()


requires, dependency_links = parse_requirements()


setup(
    name='awslimits',
    version='1.1.1',
    description='Web interface to check your AWS limits',
    author='Steve Pulec',
    author_email='spulec@gmail',
    url='https://github.com/spulec/awslimits',
    packages=['awslimits'],
    install_requires=requires,
    include_package_data=True,
    license='Apache 2.0',
    dependency_links=dependency_links,
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
)
