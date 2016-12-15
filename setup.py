#!/usr/bin/env python

from setuptools import setup

requires = [
    'boto3',
    'Flask==0.10.1',
    'Flask-WTF==0.12',
    'python-dateutil',
    'WTForms==2.1',
    'awslimitchecker',
]

setup(
    name='awslimits',
    version='1.1.0',
    description='Web interface to check your AWS limits',
    author='Steve Pulec',
    author_email='spulec@gmail',
    url='https://github.com/spulec/awslimits',
    packages=['awslimits'],
    install_requires=requires,
    include_package_data=True,
    license='Apache 2.0',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
)
