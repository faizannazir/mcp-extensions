import unittest

from openai_mcp_form_protocol import (
    FormField,
    FormSchema,
    is_valid_value,
    validate_form_selections,
)


class TestFormField(unittest.TestCase):
    def test_string_field_no_constraints(self):
        field = FormField(type="string", title="Name")
        self.assertTrue(is_valid_value(field, "hello"))
        self.assertFalse(is_valid_value(field, 123))

    def test_string_field_with_pattern(self):
        field = FormField(type="string", title="Code", pattern="^[A-Z]{3}$")
        self.assertTrue(is_valid_value(field, "ABC"))
        self.assertFalse(is_valid_value(field, "abc"))
        self.assertFalse(is_valid_value(field, "ABCD"))

    def test_string_field_with_min_max_length(self):
        field = FormField(type="string", title="Code", minLength=2, maxLength=4)
        self.assertTrue(is_valid_value(field, "AB"))
        self.assertTrue(is_valid_value(field, "ABCD"))
        self.assertFalse(is_valid_value(field, "A"))
        self.assertFalse(is_valid_value(field, "ABCDE"))

    def test_integer_field(self):
        field = FormField(type="integer", title="Age", minimum=0, maximum=150)
        self.assertTrue(is_valid_value(field, 25))
        self.assertFalse(is_valid_value(field, -1))
        self.assertFalse(is_valid_value(field, 151))
        self.assertFalse(is_valid_value(field, 25.5))

    def test_number_field(self):
        field = FormField(type="number", title="Price", minimum=0)
        self.assertTrue(is_valid_value(field, 9.99))
        self.assertFalse(is_valid_value(field, -0.01))

    def test_boolean_field(self):
        field = FormField(type="boolean", title="Active")
        self.assertTrue(is_valid_value(field, True))
        self.assertTrue(is_valid_value(field, False))
        self.assertFalse(is_valid_value(field, "true"))

    def test_enum_field(self):
        field = FormField(type="string", title="Status", enum=["active", "inactive"])
        self.assertTrue(is_valid_value(field, "active"))
        self.assertFalse(is_valid_value(field, "deleted"))

    def test_one_of_field(self):
        field = FormField(
            type="string",
            title="Color",
            oneOf=[{"const": "red", "title": "Red"}, {"const": "blue", "title": "Blue"}],
        )
        self.assertTrue(is_valid_value(field, "red"))
        self.assertFalse(is_valid_value(field, "green"))

    def test_array_field_with_items(self):
        field = FormField(
            type="array",
            title="Tags",
            items={"type": "string"},
            minItems=1,
            maxItems=3,
        )
        self.assertTrue(is_valid_value(field, ["a"]))
        self.assertTrue(is_valid_value(field, ["a", "b", "c"]))
        self.assertFalse(is_valid_value(field, []))
        self.assertFalse(is_valid_value(field, ["a", "b", "c", "d"]))

    def test_array_field_unique_items(self):
        field = FormField(
            type="array",
            title="Tags",
            items={"type": "string"},
            uniqueItems=True,
        )
        self.assertTrue(is_valid_value(field, ["a", "b"]))
        self.assertFalse(is_valid_value(field, ["a", "a"]))

    def test_array_field_with_pattern_items(self):
        field = FormField(
            type="array",
            title="Codes",
            items={"type": "string", "pattern": "^[A-Z]+$"},
        )
        self.assertTrue(is_valid_value(field, ["ABC", "DEF"]))
        self.assertFalse(is_valid_value(field, ["ABC", "abc"]))

    def test_file_input_explicit_selection(self):
        field = FormField(
            type="string",
            title="File",
            format="uri",
            **{
                "x-openai-input": {
                    "type": "resource",
                    "options": [{"uri": "file:///a.txt", "name": "a.txt"}],
                }
            },
        )
        self.assertTrue(is_valid_value(field, "file:///a.txt"))
        self.assertFalse(is_valid_value(field, "file:///b.txt"))

    def test_file_input_implicit_allows_any_uri(self):
        from openai_mcp_form_protocol import _valid_value

        field = FormField(
            type="array",
            title="Files",
            items={"type": "string", "format": "uri"},
            **{
                "x-openai-input": {
                    "type": "resource",
                    "selection": "implicit",
                    "options": [],
                }
            },
        )
        self.assertTrue(_valid_value(field, ["file:///anything.txt"]))

    def test_file_input_with_user_uploads(self):
        from openai_mcp_form_protocol import _valid_value

        field = FormField(
            type="string",
            title="File",
            format="uri",
            **{
                "x-openai-input": {
                    "type": "resource",
                    "options": [],
                    "userOptions": {"kind": "file"},
                }
            },
        )
        self.assertTrue(_valid_value(field, "file:///upload.txt", allow_user_files=True))

    def test_has_pattern_property(self):
        field = FormField(type="string", title="Code", pattern="^[a-z]+$")
        self.assertTrue(field.has_pattern)

    def test_has_pattern_false_when_no_pattern(self):
        field = FormField(type="string", title="Name")
        self.assertFalse(field.has_pattern)


class TestValidateFormSelections(unittest.TestCase):
    def test_valid_content_passes(self):
        schema = FormSchema[FormField].model_validate(
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "title": "Name"},
                    "age": {"type": "integer", "title": "Age", "minimum": 0},
                },
                "required": ["name"],
            }
        )
        validate_form_selections(schema, {"name": "Alice", "age": 30})

    def test_invalid_content_raises(self):
        schema = FormSchema[FormField].model_validate(
            {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "title": "Status",
                        "oneOf": [
                            {"const": "active", "title": "Active"},
                            {"const": "inactive", "title": "Inactive"},
                        ],
                    },
                },
            }
        )
        with self.assertRaises(ValueError):
            validate_form_selections(schema, {"status": "deleted"})

    def test_valid_enum_content_passes(self):
        schema = FormSchema[FormField].model_validate(
            {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "title": "Status",
                        "oneOf": [
                            {"const": "active", "title": "Active"},
                            {"const": "inactive", "title": "Inactive"},
                        ],
                    },
                },
            }
        )
        validate_form_selections(schema, {"status": "active"})

    def test_invalid_file_selection_raises(self):
        schema = FormSchema[FormField].model_validate(
            {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "title": "File",
                        "format": "uri",
                        "x-openai-input": {
                            "type": "resource",
                            "options": [{"uri": "file:///a.txt", "name": "a.txt"}],
                        },
                    },
                },
            }
        )
        with self.assertRaises(ValueError):
            validate_form_selections(schema, {"file": "file:///b.txt"})


if __name__ == "__main__":
    unittest.main()
