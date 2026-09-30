import unittest

from openai_mcp_extensions.mentions import (
    OpenAIMentionItem,
    OpenAIMentionResource,
    OpenAIMentionSearchParams,
    OpenAIMentionSearchResult,
)


class TestOpenAIMentionSearchParams(unittest.TestCase):
    def test_valid_params(self):
        params = OpenAIMentionSearchParams(query="users")
        self.assertEqual(params.query, "users")

    def test_empty_query_allowed(self):
        params = OpenAIMentionSearchParams(query="")
        self.assertEqual(params.query, "")


class TestOpenAIMentionSearchResult(unittest.TestCase):
    def test_empty_items(self):
        result = OpenAIMentionSearchResult(items=[])
        self.assertEqual(len(result.items), 0)

    def test_with_resource_items(self):
        result = OpenAIMentionSearchResult(
            items=[
                OpenAIMentionResource(
                    type="resource",
                    resource_uri="sql://tables/users",
                    title="users",
                )
            ]
        )
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].title, "users")

    def test_with_resource_link_items(self):
        from mcp_types import ResourceLink

        result = OpenAIMentionSearchResult(
            items=[
                ResourceLink(
                    type="resource_link",
                    uri="sql://tables/users",
                    name="users",
                )
            ]
        )
        self.assertEqual(len(result.items), 1)


class TestOpenAIMentionResource(unittest.TestCase):
    def test_valid_resource(self):
        resource = OpenAIMentionResource(
            type="resource",
            resource_uri="sql://tables/users",
            title="users",
            subtitle="User accounts",
        )
        self.assertEqual(resource.title, "users")
        self.assertEqual(resource.subtitle, "User accounts")

    def test_requires_title_and_uri(self):
        with self.assertRaises(ValueError):
            OpenAIMentionResource(type="resource", resource_uri="sql://tables/users")


if __name__ == "__main__":
    unittest.main()
