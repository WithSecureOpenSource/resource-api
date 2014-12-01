"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import os
from setuptools import setup


SRC_DIR = os.path.dirname(__file__)
CHANGES_FILE = os.path.join(SRC_DIR, "CHANGES")

with open(CHANGES_FILE) as fil:
    version = fil.readline().split()[0]


setup(
    name="resource-api-http-client",
    version=version,
    install_requires=["resource-api", "requests"],
    packages=["resource_api_http_client"],
    author="F-Secure Corporation",
    author_email="<TBD>",
    url="http://resource-api.readthedocs.org/"
)
