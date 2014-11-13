# Resource API

A framework to:
 - declaratively define resources and their relationships
 - handle resource serialization/deserialization to arbitrary data storage (e.g.: MySQL, NoSQL, plain files)
 - expose HTTP interface
 - handle authorization for individual resources

Check documentation for more detailed information.

## Code style

Run [pep8](https://pypi.python.org/pypi/pep8) and [pyflakes](https://pypi.python.org/pypi/pyflakes) in **src** directory

## Version policy

[Semantic version](http://semver.org/)

## Changelog format

```
VERSION RELEASE-TIMESTAMP=YYYY-MM-DD

    [Author Name <author@email>]
        * CHANGE_TYPE=MAJOR|MINOR|PATCH: change description
```

Example

```
12.11.3 2014-01-12

    [John Smith <john.smith@example.com>]
        * PATCH: refactored the modules
        * MINOR: added a new class
        * MAJOR: removed deprecated function
```

## Release steps

1. Increment the version in **CHANGES** file
2. Run *release.sh* to update python versions in **setup*.py** files

## Links

Travis CI: https://travis-ci.org/F-Secure/resource-api
Read the docs: http://resource-api.readthedocs.org/en/latest/