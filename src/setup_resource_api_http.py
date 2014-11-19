"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
from setuptools import setup

SOURCE_VERSION = "3.0.0"


setup(
    name="resource-api-http",
    version=SOURCE_VERSION,
    install_requires=["resource-api", "werkzeug"],
    packages=["resource_api_http"],
    author="F-Secure Corporation",
    author_email="<TBD>",
    url="http://resource-api.readthedocs.org/"
)
