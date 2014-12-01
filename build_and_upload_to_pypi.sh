#!/bin/bash

if [ "$TRAVIS_BRANCH" == "master" ]; then

    if [ -z "$PIP_PASSWORD" ]; then
      echo "PIP_PASSWORD env variable is not set. Check Travis CI settings."
    fi

    cp travis.pypirc.in ~/.pypirc
    sed -i"" "s/__PASSWORD/$PIP_PASSWORD/g" ~/.pypirc

    cp CHANGES src
    cp LICENSE src
    cp README.md src/README

    cd src

    cp setup_resource_api.py setup.py
    python setup.py sdist upload

    cp setup_resource_api_http.py setup.py
    python setup.py sdist upload

    cp setup_resource_api_http_client.py setup.py
    python setup.py sdist upload

    rm ~/.pypirc
else
    echo "Not a master branch. Uploads from branch $TRAVIS_BRANCH are not enabled."
fi
