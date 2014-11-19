#!/bin/bash

BRANCH_NAME=`git symbolic-ref --short HEAD`

if [ "$BRANCH_NAME" == "master" ]; then

    if [ -z "$PIP_PASSWORD" ]; then
      echo "PIP_PASSWORD env variable is not set. Check Travis CI settings."
    fi

    cp travis.pypirc.in ~/.pypirc
    sed -i"" "s/__PASSWORD/$PIP_PASSWORD/g" ~/.pypirc

    cd src

    cp setup_resource_api.py setup.py
    python setup.py sdist upload

    cp setup_resource_api_http.py setup.py
    python setup.py sdist upload

    cp setup_resource_api_http_client.py setup.py
    python setup.py sdist upload

    rm ~/.pypirc
else
    echo "Not a master branch. Uploads from branch $BRANCH_NAME are not enabled."
fi
