import unittest

from openai_mcp_extensions.ui import (
    OpenAIFileEntrypoint,
    OpenAIGlobalEntrypoint,
    OpenAIThreadEntrypoint,
    OpenAIUiQuickAction,
    OpenAIUiQuickActionToolTarget,
    OpenAIUiResourceMetadata,
    OpenAIUiToolMetadata,
)


class TestOpenAIGlobalEntrypoint(unittest.TestCase):
    def test_basic(self):
        ep = OpenAIGlobalEntrypoint()
        self.assertEqual(ep.type, "global")

    def test_with_quick_action(self):
        ep = OpenAIGlobalEntrypoint(
            quick_action=OpenAIUiQuickAction(
                title="New query",
                icons=[{"src": "https://example.com/icon.svg"}],
                target=OpenAIUiQuickActionToolTarget(name="sql.open"),
            )
        )
        self.assertEqual(ep.quick_action.title, "New query")


class TestOpenAIThreadEntrypoint(unittest.TestCase):
    def test_basic(self):
        ep = OpenAIThreadEntrypoint()
        self.assertEqual(ep.type, "thread")


class TestOpenAIFileEntrypoint(unittest.TestCase):
    def test_valid_extensions(self):
        ep = OpenAIFileEntrypoint(extensions=[".sql", ".csv"])
        self.assertEqual(ep.type, "file")
        self.assertEqual(len(ep.extensions), 2)

    def test_rejects_non_dot_extensions(self):
        with self.assertRaises(ValueError):
            OpenAIFileEntrypoint(extensions=["sql"])


class TestOpenAIUiToolMetadata(unittest.TestCase):
    def test_with_entrypoints(self):
        meta = OpenAIUiToolMetadata(
            entrypoints=[OpenAIGlobalEntrypoint(), OpenAIThreadEntrypoint()],
            preferred_model_display_mode="fullscreen",
        )
        self.assertEqual(len(meta.entrypoints), 2)
        self.assertEqual(meta.preferred_model_display_mode, "fullscreen")


class TestOpenAIUiResourceMetadata(unittest.TestCase):
    def test_display_modes(self):
        meta = OpenAIUiResourceMetadata(
            available_display_modes=["inline", "fullscreen"],
            preferred_display_mode="inline",
        )
        self.assertEqual(len(meta.available_display_modes), 2)


if __name__ == "__main__":
    unittest.main()
