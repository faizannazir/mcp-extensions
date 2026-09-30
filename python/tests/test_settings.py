import unittest
from typing import Any

from pydantic import BaseModel, Field

from openai_mcp_extensions.settings import (
    OpenAISettingsCapability,
    OpenAISettingsFieldPresentation,
    OpenAISettingsGroup,
    OpenAISettingsLayoutItem,
    OpenAISettingsProperty,
    OpenAISettingsReadResult,
    OpenAISettingsTool,
    OpenAISettingsUpdateArguments,
    OpenAISettingsUpdateResult,
)


class TestOpenAISettingsCapability(unittest.TestCase):
    def test_valid_capability(self):
        cap = OpenAISettingsCapability(
            read_tool="settings.read", update_tool="settings.update"
        )
        self.assertEqual(cap.read_tool, "settings.read")
        self.assertEqual(cap.update_tool, "settings.update")

    def test_rejects_blank_tool_names(self):
        with self.assertRaises(ValueError):
            OpenAISettingsCapability(read_tool="", update_tool="settings.update")


class TestOpenAISettingsReadResult(unittest.TestCase):
    def test_valid_read_result(self):
        result = OpenAISettingsReadResult(
            settings_schema={
                "type": "object",
                "properties": {
                    "units": {"type": "string", "title": "Units", "enum": ["mm", "in"]}
                },
            },
            values={"units": "mm"},
        )
        self.assertEqual(result.values["units"], "mm")

    def test_rejects_non_object_schema(self):
        with self.assertRaises(ValueError):
            OpenAISettingsReadResult(
                settings_schema={"type": "string"},
                values={},
            )

    def test_rejects_unknown_layout_property(self):
        with self.assertRaises(ValueError):
            OpenAISettingsReadResult(
                settings_schema={"type": "object", "properties": {}},
                values={},
                layout=[
                    OpenAISettingsGroup(
                        title="Group",
                        items=[OpenAISettingsProperty(property="unknown")],
                    )
                ],
            )

    def test_rejects_duplicate_layout_property(self):
        with self.assertRaises(ValueError):
            OpenAISettingsReadResult(
                settings_schema={
                    "type": "object",
                    "properties": {
                        "units": {"type": "string", "title": "Units"}
                    },
                },
                values={"units": "mm"},
                layout=[
                    OpenAISettingsGroup(
                        title="Group",
                        items=[
                            OpenAISettingsProperty(property="units"),
                            OpenAISettingsProperty(property="units"),
                        ],
                    )
                ],
            )


class TestOpenAISettingsUpdateArguments(unittest.TestCase):
    def test_valid_update(self):
        args = OpenAISettingsUpdateArguments(set={"units": "in"})
        self.assertEqual(args.set["units"], "in")

    def test_rejects_empty_set(self):
        with self.assertRaises(ValueError):
            OpenAISettingsUpdateArguments(set={})


class TestOpenAISettingsUpdateResult(unittest.TestCase):
    def test_valid_result(self):
        result = OpenAISettingsUpdateResult(values={"units": "in"})
        self.assertEqual(result.values["units"], "in")

    def test_rejects_missing_values(self):
        with self.assertRaises(ValueError):
            OpenAISettingsUpdateResult.model_validate({})


class TestOpenAISettingsFieldPresentation(unittest.TestCase):
    def test_valid_presentation(self):
        pres = OpenAISettingsFieldPresentation(title="Units")
        self.assertEqual(pres.title, "Units")
        self.assertIsNone(pres.description)

    def test_with_description(self):
        pres = OpenAISettingsFieldPresentation(
            title="Units", description="Measurement units"
        )
        self.assertEqual(pres.description, "Measurement units")


class TestOpenAISettingsLayoutItem(unittest.TestCase):
    def test_property_item(self):
        item = OpenAISettingsProperty(property="units")
        self.assertEqual(item.kind, "property")
        self.assertEqual(item.property, "units")

    def test_tool_item(self):
        item = OpenAISettingsTool(tool="cad.library", title="Browse parts")
        self.assertEqual(item.kind, "tool")
        self.assertEqual(item.tool, "cad.library")
        self.assertEqual(item.title, "Browse parts")


if __name__ == "__main__":
    unittest.main()
