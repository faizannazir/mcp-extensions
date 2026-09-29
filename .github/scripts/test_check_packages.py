"""Regression checks for package identity, independent versions, and release tags."""

import io
import json
import os
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from check_packages import check


class PackageChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.previous = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.previous)
        self.env = patch.dict(
            os.environ, {"EXPECTED_VERSION": "", "RELEASE_PACKAGE": ""}
        )
        self.env.start()
        self.addCleanup(self.env.stop)
        Path("python").mkdir()
        Path("typescript").mkdir()
        Path("packages/python").mkdir(parents=True)
        Path("packages/node").mkdir()
        Path("python/pyproject.toml").write_text(
            '[project]\nname = "openai-mcp-extensions"\nversion = "0.1.2"\n'
        )
        self.node = {
            "name": "@openai/mcp-extensions",
            "version": "0.4.0",
            "exports": {"./server": {"import": "./dist/server.js"}},
        }
        Path("typescript/package.json").write_text(json.dumps(self.node))
        Path(".release-please-manifest.json").write_text(
            json.dumps({"python": "0.1.2", "typescript": "0.4.0"})
        )
        metadata = b"Name: openai-mcp-extensions\nVersion: 0.1.2\n"
        with zipfile.ZipFile("packages/python/package.whl", "w") as wheel:
            wheel.writestr("package.dist-info/METADATA", metadata)
            wheel.writestr("openai_mcp_extensions/__init__.py", "")
            wheel.writestr("openai_mcp_form_protocol/__init__.py", "")
        self.tar("packages/python/package.tar.gz", {"package/PKG-INFO": metadata})
        self.write_node()

    def tar(self, filename, entries):
        with tarfile.open(filename, "w:gz") as archive:
            for name, data in entries.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))

    def write_node(self, include_export=True):
        entries = {
            "package/package.json": json.dumps(self.node).encode(),
            "package/LICENSE": b"",
        }
        if include_export:
            entries["package/dist/server.js"] = b"export {};"
        self.tar("packages/node/package.tgz", entries)

    def test_independent_versions_pass(self):
        check(Path("packages"))

    def test_missing_node_export_fails(self):
        self.write_node(include_export=False)
        with self.assertRaises(AssertionError):
            check(Path("packages"))

    def test_wrong_packed_version_fails(self):
        self.node["version"] = "0.4.1"
        self.write_node()
        with self.assertRaises(AssertionError):
            check(Path("packages"))

    def test_release_requires_expected_version(self):
        os.environ["RELEASE_PACKAGE"] = "python"
        with self.assertRaisesRegex(AssertionError, "expected version"):
            check(Path("packages"))

    def test_wrong_release_version_fails(self):
        os.environ.update(RELEASE_PACKAGE="python", EXPECTED_VERSION="0.4.0")
        with self.assertRaisesRegex(AssertionError, "Tag/version mismatch"):
            check(Path("packages"))

    def test_each_package_uses_its_own_tag(self):
        for package, version in (("python", "0.1.2"), ("node", "0.4.0")):
            with self.subTest(package=package):
                os.environ.update(RELEASE_PACKAGE=package, EXPECTED_VERSION=version)
                with (
                    patch(
                        "check_packages.subprocess.check_output", return_value="abc\n"
                    ) as git,
                    patch("check_packages.subprocess.run") as ancestor,
                ):
                    check(Path("packages"))
                    self.assertEqual(
                        git.call_args_list[0].args[0][-1],
                        f"refs/tags/{package}-v{version}^{{commit}}",
                    )
                    ancestor.assert_called_once_with(
                        ["git", "merge-base", "--is-ancestor", "abc", "origin/main"],
                        check=True,
                    )

    def test_tag_pointing_to_other_commit_fails(self):
        os.environ.update(RELEASE_PACKAGE="node", EXPECTED_VERSION="0.4.0")
        with (
            patch("check_packages.subprocess.check_output", side_effect=["abc", "def"]),
            self.assertRaisesRegex(AssertionError, "tested commit"),
        ):
            check(Path("packages"))


if __name__ == "__main__":
    unittest.main()
