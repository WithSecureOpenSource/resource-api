.. _errors:

Built-in exception classes
==========================

*NOTE*: do not raise framework exceptions yourself - otherwise the components might misbehave.

Framework itself raises a bunch of errors that give a descriptive information regarding the status of triggered
operations.

*NOTE*: the framework does not wrap any internal errors within implementations - they are raised without any changes.

.. automodule:: resource_api.errors
    :members:
