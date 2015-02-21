"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import re
import inspect
from copy import copy
from collections import defaultdict

import isodate
import pytz

from .errors import ValidationError, DeclarationError


class BaseField(object):
    """
    Superclass for all fields

    description (None|string = None)
        help text to be shown in schema. This should include the reasons why this field actually needs to exist.
    required (bool = False)
        flag that specifes if the field has to be present
    **kwargs
        extra parameters that are not programmatically supported
    """

    verbose_name = "unknown_type"

    def __init__(self, description=None, required=True, **kwargs):
        self.description = description
        self.kwargs = kwargs
        self.required = required

    def _to_python(self, val):
        """ Transforms primitive data (e.g. dict, list, str, int, bool, float) to a python object """
        return val

    def _validate(self, val):
        """ Validates incoming data against constraints defined via field declaration """
        if self.required and val is None:
            raise ValidationError("Value is required and thus cannot be None")

    def deserialize(self, val):
        """ Converts data passed over the wire or from the script into sth. to be used in python scripts """
        rval = self._to_python(val)
        self._validate(rval)
        return rval

    def serialize(self, val):
        """ Converts python object into sth. that can be sent over the wire """
        return val

    def get_schema(self):
        rval = {
            "description": self.description,
            "type": self.verbose_name,
            "required": self.required
        }
        rval.update(self.kwargs)
        return rval


class DateTimeField(BaseField):
    """ Represents time entity that can be either datetime or ISO 8601 datetime string.
    The item is
    `serialized <https://docs.python.org/2/library/datetime.html#datetime.datetime.isoformat>`_ into ISO 8601 string.
    """

    verbose_name = "datetime"

    def _to_python(self, val):
        val = super(DateTimeField, self)._to_python(val)
        if val is None:
            return None
        if isinstance(val, basestring):
            try:
                # Parse datetime
                val = isodate.parse_datetime(val)
            except ValueError:
                raise ValidationError("Timestamp has to be a string in ISO 8601 format")

        # Convert to naive UTC
        if val.tzinfo:
            val = val.astimezone(pytz.utc)
            val = val.replace(tzinfo=None)
        return val

    def serialize(self, val):
        if val is None:
            return None
        return val.isoformat()


class BaseSimpleField(BaseField):

    python_type = None

    def __init__(self, default=None, **kwargs):
        super(BaseSimpleField, self).__init__(**kwargs)
        try:
            self.default = self._to_python(default)
        except ValidationError, e:
            raise DeclarationError("default: %s" % str(e))

    def _to_python(self, val):
        if val is None:
            return None
        try:
            return self.python_type(val)
        except ValueError:
            raise ValidationError("Converion of value %r failed" % val)

    def get_schema(self):
        rval = super(BaseSimpleField, self).get_schema()
        rval["default"] = self.default
        return rval


class IndexableField(BaseSimpleField):

    def __init__(self, choices=None, invalid_choices=None, **kwargs):
        super(IndexableField, self).__init__(**kwargs)

        if choices is not None:
            if not isinstance(choices, (list, tuple)):
                raise DeclarationError("choices has to be a list or tuple")
            tempo = []
            for i in xrange(len(choices)):
                try:
                    tempo.append(self._to_python(choices[i]))
                except Exception, e:
                    raise DeclarationError("[%d]: %s" % (i, str(e)))
            choices = tempo

        if invalid_choices is not None:
            if not isinstance(invalid_choices, (list, tuple)):
                raise DeclarationError("invalid_choices has to be a list or tuple")
            tempo = []
            for i in xrange(len(invalid_choices)):
                try:
                    tempo.append(self._to_python(invalid_choices[i]))
                except Exception, e:
                    raise DeclarationError("[%d]: %s" % (i, str(e)))
            invalid_choices = tempo

        if self.default is not None:
            if invalid_choices and self.default in invalid_choices:
                raise DeclarationError("default value is in invalid_choices")
            if choices and self.default not in choices:
                raise DeclarationError("default value is not in choices")

        if invalid_choices and choices:
            inter = set(choices).intersection(set(invalid_choices))
            if inter:
                raise DeclarationError("these choices are stated as both valid and invalid: %r" % inter)

        self.choices, self.invalid_choices = choices, invalid_choices

    def _validate(self, val):
        super(IndexableField, self)._validate(val)
        if val is None:
            return
        if self.choices and val not in self.choices:
            raise ValidationError("Val %r must be one of %r" % (val, self.choices))
        if self.invalid_choices and val in self.invalid_choices:
            raise ValidationError("Val %r must NOT be one of %r" % (val, self.invalid_choices))

    def get_schema(self):
        rval = super(IndexableField, self).get_schema()
        rval["choices"] = self.choices
        rval["invalid_choices"] = self.invalid_choices
        return rval


class DigitField(IndexableField):
    """ Base class for fields that represent numbers

    min_val (int|long|float = None)
        Minumum threshold for incoming value
    max_val (int|long|float = None)
        Maximum threshold for imcoming value
    """

    def __init__(self, min_val=None, max_val=None, **kwargs):
        super(DigitField, self).__init__(**kwargs)
        min_val = self._to_python(min_val)
        max_val = self._to_python(max_val)

        value_check = min_val or max_val
        if self.choices is not None and value_check is not None:
            raise DeclarationError("choices and min or max value limits do not make sense together")
        if min_val is not None and max_val is not None:
            if max_val < min_val:
                raise DeclarationError("max val is less than min_val")

        if self.default is not None:
            if min_val is not None and self.default < min_val:
                raise DeclarationError("default value is too small")
            if max_val is not None and self.default > max_val:
                raise DeclarationError("default value is too big")

        self.min_val, self.max_val = min_val, max_val

    def _to_python(self, val):
        if not isinstance(val, (basestring, int, long, float, type(None))):
            raise ValidationError("Has to be a digit or a string convertable to digit")
        return super(DigitField, self)._to_python(val)

    def _validate(self, val):
        super(DigitField, self)._validate(val)
        if val is None:
            return
        if self.min_val is not None and val < self.min_val:
            raise ValidationError("Digit %r is too small. Has to be at least %r." % (val, self.min_val))
        if self.max_val is not None and val > self.max_val:
            raise ValidationError("Digit %r is too big. Has to be at max %r." % (val, self.max_val))

    def get_schema(self):
        rval = super(DigitField, self).get_schema()
        rval.update({
            "min_val": self.min_val,
            "max_val": self.max_val
        })
        return rval


class IntegerField(DigitField):
    """ Transforms input data that could be any number or a string value with that number into *long* """
    python_type = long
    verbose_name = "int"


class FloatField(DigitField):
    """ Transforms input data that could be any number or a string value with that number into *float* """
    python_type = float
    verbose_name = "float"


class StringField(IndexableField):
    """ Represents any arbitrary text

    regex (string = None)
        `Python regular expression <https://docs.python.org/2/library/re.html#regular-expression-syntax>`_
        used to validate the string.
    min_length (int = None)
        Minimum size of string value
    max_length (int = None)
        Maximum size of string value
    """
    python_type = unicode
    verbose_name = "string"

    def __init__(self, regex=None, min_length=None, max_length=None, **kwargs):
        super(StringField, self).__init__(**kwargs)

        def _set(name, transform_f, val):
            if val is not None:
                try:
                    val = transform_f(val)
                except Exception, e:
                    raise DeclarationError("%s: %s" % (name, str(e)))
            setattr(self, name, val)

        val_check = min_length or max_length or regex

        if self.choices and val_check is not None:
            raise DeclarationError("choices and value checkers do not make sense together")

        _set("regex", re.compile, regex)
        _set("min_length", int, min_length)
        _set("max_length", int, max_length)

    def _to_python(self, val):
        if not isinstance(val, (basestring, type(None))):
            raise ValidationError("Has to be string")
        return super(StringField, self)._to_python(val)

    def _validate(self, val):
        super(StringField, self)._validate(val)
        if val is None:
            return
        if self.min_length is not None:
            if len(val) < self.min_length:
                raise ValidationError("Length is too small. Is %r has to be at least %r." % (len(val),
                                                                                             self.min_length))
        if self.max_length is not None:
            if len(val) > self.max_length:
                raise ValidationError("Length is too small. Is %r has to be at least %r." % (len(val),
                                                                                             self.max_length))
        reg = self.regex
        if reg is not None:
            if not reg.match(val):
                raise ValidationError("%r did not match regexp %r" % (val, reg.pattern))

    def get_schema(self):
        rval = super(StringField, self).get_schema()
        rval.update({
            "regex": getattr(self.regex, "pattern", None),
            "min_length": self.min_length,
            "max_length": self.max_length})
        return rval


class BooleanField(BaseSimpleField):
    """ Expects only a boolean value as incoming data """
    verbose_name = "boolean"
    python_type = bool

    def _to_python(self, val):
        if not isinstance(val, (bool, type(None))):
            raise ValidationError("Has to be a digit or a string convertable to digit")
        return super(BooleanField, self)._to_python(val)


PRIMITIVE_TYPES_MAP = {
    int: IntegerField,
    float: FloatField,
    str: StringField,
    unicode: StringField,
    basestring: StringField,
    bool: BooleanField
}


def wrap_into_field(simple_type):
    if not isinstance(simple_type, BaseField):
        field_class = PRIMITIVE_TYPES_MAP.get(simple_type, None)
        if field_class:
            return field_class()
        else:
            return ObjectField(simple_type)
    return simple_type


class ListField(BaseField):
    """ Represents a collection of primitives. Serialized into a list.

    item_type (python primitve|Field instance)
        value is used by list field to validate individual items
        python primitive are internally mapped to Field instances according to
        :data:`PRIMITIVE_TYPES_MAP <resource_api.interfaces.PRIMITIVE_TYPES_MAP>`
    """

    verbose_name = "list"

    def __init__(self, item_type, **kwargs):
        super(ListField, self).__init__(**kwargs)
        self.item_type = wrap_into_field(item_type)

    def deserialize(self, val):
        self._validate(val)
        if val is None:
            return val
        errors = []
        rval = []
        if not isinstance(val, list):
            raise ValidationError("Has to be list")
        for item in val:
            try:
                rval.append(self.item_type.deserialize(item))
            except ValidationError, e:
                errors.append([val.index(item), e.message])
        if errors:
            raise ValidationError(errors)
        return rval

    def get_schema(self):
        rval = super(ListField, self).get_schema()
        rval["schema"] = self.item_type.get_schema()
        return rval

    def serialize(self, val):
        return [self.item_type.serialize(item) for item in val]


class ObjectField(BaseField):
    """ Represents a nested document/mapping of primitives. Serialized into a dict.

    schema (class):
        schema to be used for validation of the nested document, it does not have to be Schema subclass - just a
        collection of fields

    ObjectField can be declared via two different ways.

    First, if there is a reusable schema defined elsewhere:

    >>> class Sample(Schema):
    >>>     object_field = ObjectField(ExternalSchema, required=False, description="Zen")

    Second, if the field is supposed to have a unique custom schema:

    >>> class Sample(Schema):
    >>>     object_field = ObjectField(required=False, description="Zen", schema=dict(
    >>>         "foo": StringField()
    >>>     ))
    """

    verbose_name = "dict"

    def __init__(self, schema, **kwargs):
        super(ObjectField, self).__init__(**kwargs)

        if isinstance(schema, dict):
            class tmp(Schema):
                pass
            for key, value in schema.iteritems():
                setattr(tmp, key, value)
            schema = tmp
        elif inspect.isclass(schema) and not issubclass(schema, Schema):
            class tmp(schema, Schema):
                pass
            schema = tmp
        self._schema = schema()

    def deserialize(self, val):
        self._validate(val)
        if val is None:
            return val
        return self._schema.deserialize(val)

    def get_schema(self):
        return {
            "type": self.verbose_name,
            "schema": self._schema.get_schema()
        }

    def serialize(self, val):
        return self._schema.serialize(val)


class Schema(object):
    """ Base class for containers that would hold one or many fields.

    it has one class attribute that may be used to alter shcema's validation flow

    has_additional_fields (bool = False)
        If *True* it shall be possible to have extra fields inside input data that will not be validated

    NOTE: when defining schemas do not use any of the following reserved keywords:

        - find_fields
        - deserialize
        - get_schema
        - serialize
        - has_additional_fields
    """

    has_additional_fields = False

    def __init__(self, validate_required_constraint=True, with_errors=True):
        self._required_fields = set()
        self._defaults = {}
        self._validate_required_constraint, self._with_errors = validate_required_constraint, with_errors

        self.fields = {}

        for field_name in dir(self):
            field = getattr(self, field_name)
            if not isinstance(field, BaseField):
                continue
            self._add_field(field_name, copy(field))

    def _add_field(self, field_name, field):
        setattr(self, field_name, field)
        self.fields[field_name] = field
        if isinstance(field, BaseField) and field.required:
            self._required_fields.add(field_name)
        if isinstance(field, BaseSimpleField) and field.default is not None:
            self._defaults[field_name] = field.default

    def find_fields(self, **kwargs):
        """ Returns a set of fields where each field contains one or more specified keyword arguments """
        rval = set()
        for key, value in kwargs.iteritems():
            for field_name, field in self.fields.iteritems():
                if field.kwargs.get(key) == value:
                    rval.add(field_name)
        return rval

    def deserialize(self, data, validate_required_constraint=True, with_errors=True):
        """ Validates and transforms input data into something that is used withing data access layer

        data (dict)
            Incoming data
        validate_required_constraint (bool = True)
            If *False*, schema will not validate required constraint of the fields inside
        with_errors (bool = True)
            If *False*, all fields that contain errors are silently excluded

        @raises ValidationError
            When one or more fields has errors and *with_errors=True*
        """

        if not isinstance(data, dict):
            raise ValidationError({"__all__": "Has to be a dict"})

        transformed = dict(self._defaults)
        errors = defaultdict(list)

        for key, value in data.iteritems():
            field = self.fields.get(key)

            if field is None:
                if self.has_additional_fields:
                    transformed[key] = value
                else:
                    errors["__all__"].append("Field %r is not defined" % key)
                continue

            try:
                transformed[key] = field.deserialize(value)
            except ValidationError, e:
                errors[key].append(e.message)

        if validate_required_constraint:
            for field in self._required_fields:
                if transformed.get(field) is None and field not in errors:
                    errors[field].append("Required field is missing")

        if errors and with_errors:
            raise ValidationError(errors)
        else:
            return transformed

    def get_schema(self):
        """ Returns a JSONizable schema that could be transfered over the wire """
        rval = {}
        for field_name, field in self.fields.iteritems():
            rval[field_name] = field.get_schema()
        if self.has_additional_fields:
            rval["has_additional_fields"] = True
        return rval

    def serialize(self, val):
        """ Transforms outgoing data into a JSONizable dict """
        rval = {}
        for key, value in val.iteritems():
            field = self.fields.get(key)
            if field:
                rval[key] = field.serialize(value)
            elif self.has_additional_fields:
                rval[key] = value
            else:
                pass
        return rval
