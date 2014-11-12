.. _schema:

Schema
======

A collection of fields is represented by:

.. autoclass:: resource_api.schema.Schema

Schema example
--------------

A schema for a page with title, text, creation timestamp and a 5 star rating would look the following way:

.. code-block:: python

    class PageSchema(Schema):
        title = StringField(max_length=70)
        text = StringField()
        creation_time = DateTimeField()
        rating = IntegerField(min_value=1, max_value=5)

General field API
-----------------

All fields inherit from *BaseField* and thus have its attributes in common.

.. autoclass:: resource_api.schema.BaseField

There are two extra parameters supported by Resource API:

readonly (bool=False)
    if True field cannot be set nor changed but is a logical part of the resource. Resource creation time would be
    a good example.

changeable (bool=False)
    if True field can be set during creation but cannot be change later on. User's birth date is a valid example.

Primitive fields
----------------

There are two types of digit fields supported by schema. Integers and floats. Fields that represent them have a common
base class:

.. autoclass:: resource_api.schema.DigitField

The fields representing integers and floats respecively are:

.. autoclass:: resource_api.schema.IntegerField
.. autoclass:: resource_api.schema.FloatField

----------

Time is represented by:

.. autoclass:: resource_api.schema.DateTimeField

----------

Strings are represented by:

.. autoclass:: resource_api.schema.StringField

----------

Various boolean flags exist in the schape of:

.. autoclass:: resource_api.schema.BooleanField

Composite fields
----------------

.. autoclass:: resource_api.schema.ListField

.. code-block:: python

    PRIMITIVE_TYPES_MAP = {
        int: IntegerField,
        float: FloatField,
        str: StringField,
        unicode: StringField,
        basestring: StringField,
        bool: BooleanField
    }

.. autoclass:: resource_api.schema.ObjectField
