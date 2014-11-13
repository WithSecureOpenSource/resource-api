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

1. Merge **dev** into **master**
2. Switch to **master**
3. Make sure that all checks and tests pass
4. Increment the version in **CHANGES** file according to the types of changes made since the latest release
5. Run *release.sh* to update python versions in **setup*.py** files
6. Commit the changes
7. Execute "git tag VERSION -m VERSION"
8. Switch to **dev**
9. Add a new changelog entry that is just slightly higher than the released one (without release timestamp)
10. Commit the changes
11. Push **dev** & **maste** branches
12. Push tags

## Pull requests

Always create your own feature branches from the **dev** branch. Not from **master** one.

1. Make sure that all commits have descriptive messages and are up to the point
2. pep8 and pyflakes checks are supposed to pass
3. All tests are supposed to pass
4. If it is a new feature - make sure that new tests are created and they pass
5. Add a new set of bullet points to the latest changelog entry according to the specified format
6. Create a pull request against the **dev** branch

## Links

- Travis CI: https://travis-ci.org/F-Secure/resource-api
- Read the docs: http://resource-api.readthedocs.org/en/latest/