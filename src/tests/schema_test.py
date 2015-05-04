"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import unittest
from datetime import datetime, date, time

import pytz

from resource_api.schema import(IntegerField, FloatField, StringField, BooleanField, ListField, Schema,
                                DateTimeField, ObjectField, DateField, TimeField, DurationField)
from resource_api.errors import ValidationError, DeclarationError


class PropertyFieldTest(object):

    ok_val = nok_val = field_class = transformed_val = None

    def test_optional_empty_value(self):
        field = self.field_class(required=False)
        self.assertEqual(field.deserialize(None), None)

    def test_required_empty_value(self):
        field = self.field_class()
        self.assertRaises(ValidationError, field.deserialize, None)

    def test_normal_value(self):
        field = self.field_class(required=True)
        val = self.transformed_val or self.ok_val
        self.assertEqual(field.deserialize(self.ok_val), val)

    def test_description(self):
        field = self.field_class(description="bla")
        self.assertEqual(field.description, "bla")

    def test_serialize(self):
        field = self.field_class()
        self.assertEqual(field.serialize(self.transformed_val or self.ok_val), self.ok_val)


class BaseSimpleFieldTest(PropertyFieldTest):

    def test_empty_default_value(self):
        field = self.field_class()
        self.assertEqual(field.default, None)

    def test_wrong_default_value(self):
        self.assertRaises(DeclarationError, self.field_class, default=self.nok_val)

    def test_default_value(self):
        field = self.field_class(default=self.ok_val)
        self.assertEqual(field.get_schema()["default"], self.ok_val)


class BaseIsoFieldTest(PropertyFieldTest):

    def test_naive_input(self):
        field = self.field_class()
        self.assertEqual(field.deserialize(self.transformed_val), self.transformed_val)


class DateTimeFieldTest(BaseIsoFieldTest, unittest.TestCase):
    transformed_val = datetime(2013, 9, 30, 11, 32, 39, 984847)
    ok_val = "2013-09-30T11:32:39.984847"
    nok_val = "BAD STRING"
    field_class = DateTimeField

    def test_string_timezone_input(self):
        field = self.field_class()
        expected = datetime(2013, 9, 30, 8, 32, 39, 984847)
        self.assertEqual(field.deserialize('2013-09-30T11:32:39.984847+0300'), expected)

    def test_utc_timezone_input(self):
        field = self.field_class()
        dt = datetime(2014, 1, 1, 11, 32, 39, 984847, tzinfo=pytz.utc)
        expected = datetime(2014, 1, 1, 11, 32, 39, 984847)
        self.assertEqual(field.deserialize(dt), expected)

    def test_timezone_input(self):
        field = self.field_class()
        dt = datetime(2014, 1, 1, 11, 32, 39, 984847, tzinfo=pytz.utc)
        dt = dt.astimezone(pytz.timezone('Europe/Helsinki'))
        expected = datetime(2014, 1, 1, 11, 32, 39, 984847)
        self.assertEqual(field.deserialize(dt), expected)

    def test_timezone_dst_input(self):
        field = self.field_class()
        dt = datetime(2014, 7, 1, 11, 32, 39, 984847, tzinfo=pytz.utc)
        dt = dt.astimezone(pytz.timezone('Europe/Helsinki'))
        expected = datetime(2014, 7, 1, 11, 32, 39, 984847)
        self.assertEqual(field.deserialize(dt), expected)


class DateFieldTest(BaseIsoFieldTest, unittest.TestCase):
    transformed_val = date(2013, 9, 30)
    ok_val = "2013-09-30"
    nok_val = "BAD STRING"
    field_class = DateField


class TimeFieldTest(BaseIsoFieldTest, unittest.TestCase):
    transformed_val = time(12, 11, 10)
    ok_val = "12:11:10"
    nok_val = "BAD STRING"
    field_class = TimeField

    def test_string_timezone_input(self):
        field = self.field_class()
        expected = time(8, 32, 39, 984847)
        self.assertEqual(field.deserialize('11:32:39.984847+0300'), expected)

    def test_utc_timezone_input(self):
        field = self.field_class()
        t = time(11, 32, 39, 984847, tzinfo=pytz.utc)
        expected = time(11, 32, 39, 984847)
        self.assertEqual(field.deserialize(t), expected)

    def _get_tz(self, val, tz):
        dt = datetime.combine(date(2015, 2, 2), val)
        dt = dt.astimezone(tz)
        dt = dt.replace(tzinfo=None)
        return dt.time()

    def test_timezone_input(self):
        field = self.field_class()
        t = time(11, 32, 39, 984847, tzinfo=pytz.utc)
        t = self._get_tz(t, pytz.timezone('Europe/Helsinki'))
        expected = time(13, 32, 39, 984847)
        self.assertEqual(field.deserialize(t), expected)

    def test_timezone_dst_input(self):
        field = self.field_class()
        t = time(11, 32, 39, 984847, tzinfo=pytz.utc)
        t = self._get_tz(t, pytz.timezone('Europe/Helsinki'))
        expected = time(13, 32, 39, 984847)
        self.assertEqual(field.deserialize(t), expected)


class DurationFieldTest(BaseIsoFieldTest, unittest.TestCase):
    transformed_val = datetime(2015, 10, 9) - datetime(2014, 11, 11)
    ok_val = "P332D"
    nok_val = "BAD STRING"
    field_class = DurationField


class IndexableFieldTest(BaseSimpleFieldTest):

    nok_choices = ok_choices = ok_choice_value = nok_choice_value = None

    def test_invalid_choices(self):
        field = self.field_class(invalid_choices=self.ok_choices)
        self.assertRaises(ValidationError, field.deserialize, self.ok_choices[0])

    def test_wrong_choices(self):
        # not a list
        self.assertRaises(DeclarationError, self.field_class, choices="WTH?")
        # wrong item types
        self.assertRaises(DeclarationError, self.field_class, choices=self.nok_choices)

    def test_wrong_invalid_choices(self):
        # not a list
        self.assertRaises(DeclarationError, self.field_class, invalid_choices="WTH?")
        # wrong item types
        self.assertRaises(DeclarationError, self.field_class, invalid_choices=self.nok_choices)

    def test_not_in_choices(self):
        field = self.field_class(choices=self.ok_choices)
        self.assertRaises(ValidationError, field.deserialize, self.nok_choice_value)

    def test_in_choices(self):
        field = self.field_class(choices=self.ok_choices)
        field.deserialize(self.ok_choice_value)

    def test_default_value_in_invalid_choices(self):
        self.assertRaises(DeclarationError, self.field_class, invalid_choices=self.ok_choices,
                          default=self.ok_choices[0])

    def test_default_value_not_in_choices(self):
        self.assertRaises(DeclarationError, self.field_class, choices=self.ok_choices, default=self.nok_choice_value)

    def test_choices_and_invalid_choices_conflict(self):
        self.assertRaises(DeclarationError, self.field_class, choices=self.ok_choices, invalid_choices=self.ok_choices)

    def test_schema_choices(self):
        field = self.field_class(choices=self.ok_choices)
        self.assertEqual(field.get_schema()["choices"], self.ok_choices)
        field = self.field_class(invalid_choices=self.ok_choices)
        self.assertEqual(field.get_schema()["invalid_choices"], self.ok_choices)


class DigitFieldTest(IndexableFieldTest):

    nok_val = "BLA"
    ok_choices = range(10)
    nok_choices = "BLA"

    def test_wrong_min_and_max(self):
        self.assertRaises(ValidationError, self.field_class, min_val=self.nok_val)
        self.assertRaises(ValidationError, self.field_class, max_val=self.nok_val)

    def test_too_small_val(self):
        field = self.field_class(min_val=6)
        self.assertRaises(ValidationError, field.deserialize, 4)

    def test_too_big_val(self):
        field = self.field_class(max_val=5)
        self.assertRaises(ValidationError, field.deserialize, 8)

    def test_ok_val(self):
        field = self.field_class(max_val=8, min_val=5)
        self.assertEqual(field.deserialize(self.ok_val), self.ok_val)

    def test_choices_and_range(self):
        self.assertRaises(DeclarationError, self.field_class, choices=self.ok_choices, min_val=self.ok_val)
        self.assertRaises(DeclarationError, self.field_class, choices=self.ok_choices, max_val=self.ok_val)

    def test_min_max_conflict(self):
        self.assertRaises(DeclarationError, self.field_class, min_val=16, max_val=3)

    def test_default_value_not_in_range(self):
        self.assertRaisesRegexp(DeclarationError, "too small", self.field_class, min_val=8, max_val=16, default=5)
        self.assertRaisesRegexp(DeclarationError, "too big", self.field_class, min_val=8, max_val=16, default=25)

    def test_wrong_input_type(self):
        field = self.field_class()
        self.assertRaisesRegexp(ValidationError, "Has to be a digit or a string convertable to digit",
                                field.deserialize, object())

    def test_min_max_schema(self):
        field = self.field_class(min_val=8, max_val=16)
        schema = field.get_schema()
        self.assertEqual(schema["min_val"], 8)
        self.assertEqual(schema["max_val"], 16)


class IntegerFieldTest(DigitFieldTest, unittest.TestCase):

    ok_val = 5
    ok_choice_value = 7
    nok_choice_value = 11
    field_class = IntegerField


class FloatFieldTest(DigitFieldTest, unittest.TestCase):

    ok_val = 5.1
    ok_choice_value = 7.0
    nok_choice_value = 11.1
    field_class = FloatField


class BooleanFieldTest(BaseSimpleFieldTest, unittest.TestCase):
    ok_val = True
    nok_val = "BLA"
    field_class = BooleanField


class StringFieldTest(IndexableFieldTest, unittest.TestCase):

    ok_val = "BLA"
    nok_val = 96
    ok_choices = ["BLA", "Bal", "Fel"]
    nok_choices = range(3)
    ok_choice_value = "BLA"
    nok_choice_value = "Foo"
    field_class = StringField

    def test_too_short(self):
        field = self.field_class(min_length=10)
        self.assertRaises(ValidationError, field.deserialize, "BLA")

    def test_too_long(self):
        field = self.field_class(max_length=10)
        self.assertRaises(ValidationError, field.deserialize, "b" * 40)

    def test_ok_length(self):
        field = self.field_class(min_length=10, max_length=40)
        field.deserialize("b" * 20)

    def test_regexp_no_match(self):
        field = self.field_class(regex="^[a-z]+$")
        self.assertRaises(ValidationError, field.deserialize, "642")

    def test_regexp_match(self):
        field = self.field_class(regex="^[a-z]+$")
        field.deserialize("abracadabra")

    def test_get_schema(self):
        field = self.field_class(regex="^[a-z]+$", min_length=16, max_length=36)
        self.assertEqual(field.get_schema(), {
            'description': None,
            'required': True,
            'choices': None,
            'invalid_choices': None,
            'default': None,
            'min_length': 16,
            'max_length': 36,
            'regex': '^[a-z]+$',
            'type': 'string'})

    def test_wrong_regex_declaration(self):
        self.assertRaisesRegexp(DeclarationError, "regex: first argument must be string or compiled pattern",
                                self.field_class, regex=16)

    def test_wrong_length_declaration(self):
        self.assertRaisesRegexp(DeclarationError, "min_length: invalid literal for int()",
                                self.field_class, min_length="FOO")
        self.assertRaisesRegexp(DeclarationError, "max_length: invalid literal for int()",
                                self.field_class, max_length="FOO")

    def test_choices_and_value_check(self):
        self.assertRaises(DeclarationError, self.field_class, choices=self.ok_choices, min_length=16)


class ListFieldTest(PropertyFieldTest, unittest.TestCase):

    ok_val = range(10)
    nok_val = "BLA"

    def field_class(self, **kwargs):
        return ListField(int, **kwargs)

    def test_non_list(self):
        field = self.field_class()
        self.assertRaises(ValidationError, field.deserialize, self.nok_val)

    def test_wrong_item_type(self):
        field = self.field_class()
        self.assertRaises(ValidationError, field.deserialize, ["WUGA"])

    def test_proper_list(self):
        field = self.field_class()
        field.deserialize(self.ok_val)

    def test_with_field_object(self):
        field = ListField(StringField())
        field.deserialize(["WUGA"])

    def test_list_of_items_with_schema(self):

        class TempSchema(Schema):
            required_field = StringField(required=True)

        field = ListField(TempSchema)
        self.assertRaises(ValidationError, field.deserialize, [1, 2])
        self.assertEqual(field.get_schema()["schema"], ObjectField(TempSchema).get_schema())
        field.deserialize([{"required_field": "foo"}, {"required_field": "bar"}])


class TestFieldSchema:
    has_additional_fields = True
    two = ListField(int)


class ObjectFieldTest(PropertyFieldTest, unittest.TestCase):

    ok_val = {"two": [1, 2, 3]}
    nok_val = "BLA"

    def field_class(self, **kwargs):
        return ObjectField(TestFieldSchema, **kwargs)

    def test_schema(self):
        field = self.field_class()
        schema = field.get_schema()
        self.assertEqual(schema, {
            "type": "dict",
            "schema": {
                "two": {'type': 'list', 'description': None, 'required': True,
                        'schema': {'type': 'int', 'description': None, 'choices': None, 'default': None,
                                   'invalid_choices': None, 'max_val': None, 'min_val': None, 'required': True}},
                "has_additional_fields": True
            }
        })

    def test_dict_schema(self):
        field = ObjectField(dict(
            two=ListField(int),
            has_additional_fields=True
        ))
        schema = field.get_schema()
        from pprint import pprint
        print pprint(schema)
        self.assertEqual(schema, {
            "type": "dict",
            "schema": {
                "two": {'type': 'list', 'description': None, 'required': True,
                        'schema': {'type': 'int', 'description': None, 'choices': None, 'default': None,
                                   'invalid_choices': None, 'max_val': None, 'min_val': None, 'required': True}},
                "has_additional_fields": True
            }
        })


class SchemaTest(unittest.TestCase):

    def test_required_data(self):

        class TempSchema(Schema):
            required_field = StringField(required=True)

        schema = TempSchema()

        self.assertRaises(ValidationError, schema.deserialize, {})

    def test_default_required_data(self):

        class TempSchema(Schema):
            default_required_field = StringField(required=True, default="BLA")

        schema = TempSchema()

        schema.deserialize({})
        self.assertRaises(ValidationError, schema.deserialize, {"default_required_field": None})

    def test_extra_fields_data(self):

        class TempSchema(Schema):
            item_field = StringField(required=False)

        schema = TempSchema()

        self.assertRaises(ValidationError, schema.deserialize, {"nonexistent_data": "bla"})

    def test_validate_required_constraint(self):

        class TempSchema(Schema):
            required_field = StringField(required=True)

        schema = TempSchema()

        schema.deserialize({}, validate_required_constraint=False)

    def test_schema_with_non_base_fields(self):

        class TempSchema(Schema):
            required_field = StringField(required=False)
            foo = 123

            def bar(self):
                pass

        schema = TempSchema()

        self.assertRaises(ValidationError, schema.deserialize, {"foo": 123, "bar": 123})
        schema.deserialize({})

    def test_schema_with_wildcard_fields(self):

        class WildCardSchema(Schema):
            has_additional_fields = True

            one = IntegerField()

        schema = WildCardSchema()
        data = {"one": 1, "baga": "wuga", "muga": "haga"}
        rval = schema.deserialize(data)
        self.assertEqual(rval, data)
        self.assertRaises(ValidationError, schema.deserialize,
                          {"baga": "wuga", "muga": "haga"})

    def test_schema_without_errors(self):
        class SchemaWithoutErrors(Schema):
            one = IntegerField()
            two = StringField()

        schema = SchemaWithoutErrors()
        data = {"one": 1, "two": 666, "muga": "haga"}
        schema.deserialize(data, with_errors=False)
        self.assertEqual(schema.deserialize(data, with_errors=False), {"one": 1})
        self.assertRaises(ValidationError, schema.deserialize,
                          data)

    def test_schema_serialization(self):
        class Sample(Schema):
            one = IntegerField()
            two = StringField()
            three = DateTimeField()
        schema = Sample()
        self.assertEqual(
            schema.serialize({"one": 1, "two": "two", "three": datetime(2010, 12, 1), "foo": "bar"}),
            {"one": 1, "two": "two", "three": "2010-12-01T00:00:00"}
        )

    def test_schema_serialization_without_extra_data(self):
        class Sample(Schema):
            one = IntegerField()
            two = StringField()
            three = DateTimeField()
        schema = Sample()
        self.assertEqual(
            schema.serialize({"one": 1, "two": "two", "three": datetime(2010, 12, 1), "foo": "bar"}),
            {"one": 1, "two": "two", "three": "2010-12-01T00:00:00"}
        )

    def test_schema_serialization_with_extra_data(self):
        class Sample(Schema):
            one = IntegerField()
            two = StringField()
            three = DateTimeField()
            has_additional_fields = True
        schema = Sample()
        self.assertEqual(
            schema.serialize({"one": 1, "two": "two", "three": datetime(2010, 12, 1), "foo": "bar"}),
            {"one": 1, "two": "two", "three": "2010-12-01T00:00:00", "foo": "bar"}
        )
