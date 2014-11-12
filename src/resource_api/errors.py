"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""


class FrameworkError(Exception):
    " Base class for all the errors that are raised by the framework "


class MultipleFound(FrameworkError):
    " Raised when user tries to fetch link to one instance and the framework manages to find multiple entries "


class ValidationError(FrameworkError):
    " Raised for any issue related to data sent by user including linking errors "


class DoesNotExist(FrameworkError):
    " Raised when trying to fetch a non-existent Resource or Link instance "


class DataConflictError(FrameworkError):
    """ Raised when user tries to perform something that conflicts with a current state of data
    - create Resource or Link that was already create before
    """


class Forbidden(FrameworkError):
    """ Raised whenever user tries to perform something that is prohibited due to the structure of data
    - remove required LinkToOne
    - create one to many link
    """


class AuthorizationError(FrameworkError):
    " Raised when user is not allowed to perform a specific operation with resource instance or resource collection "


class DeclarationError(FrameworkError):
    " Raised by the framework during initialization phase if there are some issues with declarations "


class ResourceDeclarationError(DeclarationError):
    " Raised by the framework when there are issues with resource declarations "

    def __init__(self, resource, message):
        self._resource = resource
        self._message = message

    def __str__(self):
        return "%s: %s" % (str(self._resource.get_name()), self._message)
