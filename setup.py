#!/usr/bin/python
# Copyright (c) 2013 Vindeka, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages
name = 'gateswift'
version = '0.1'

setup(
    name=name,
    version=version,
    description='Gate Forensics Suite - Swift Middleware',
    license='Apache License (2.0)',
    author='Vindeka, LLC',
    author_email='dev@vindeka.com',
    url='http://vindeka.com/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Environment :: No Input/Output (Daemon)',
        ],
    install_requires=[],
    entry_points={
        'paste.app_factory': ['main=identity:app_factory'],
        'paste.filter_factory': [
            'gatemiddleware=gateswift.middleware:filter_factory',
            ],
        },
    )
