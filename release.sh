#!/bin/bash

version=`cat CHANGES | head -n1 | cut -f 1 -d " "`

sed -i "s/SOURCE_VERSION = .*/SOURCE_VERSION = \"$version\"/g" src/setup_*.py
sed -i "s/version = .*/version = '$version'/g" documentation/conf.py
