"""Validate the actual release archives, including version and exported files."""

import email
import json
import os
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def check(packages: Path) -> None:
    project = tomllib.loads(Path("python/pyproject.toml").read_text())["project"]
    node = json.loads(Path("typescript/package.json").read_text())
    manifest = json.loads(Path(".release-please-manifest.json").read_text())
    version = project["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), (
        "Only stable release versions are supported"
    )
    node_version = node["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", node_version)
    assert manifest == {"python": version, "typescript": node_version}, (
        "Release manifest is stale"
    )
    expected = os.environ.get("EXPECTED_VERSION")
    if os.environ.get("RELEASE_PACKAGE"):
        assert expected, "A release requires an expected version"
    if expected:
        assert re.fullmatch(r"\d+\.\d+\.\d+", expected), "Invalid release version"
        package = os.environ["RELEASE_PACKAGE"]
        assert package in ("python", "node")
        assert expected == (version if package == "python" else node_version), (
            "Tag/version mismatch"
        )
        tag = f"refs/tags/{package}-v{expected}"
        tagged = subprocess.check_output(
            ["git", "rev-parse", f"{tag}^{{commit}}"], text=True
        ).strip()
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        assert tagged == head, "Release tag must identify the tested commit"
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", head, "origin/main"], check=True
        )
    assert project["name"] == "openai-mcp-extensions"
    assert node["name"] == "@openai/mcp-extensions"
    assert not node.get("private"), "The Node package must be publishable"

    wheels = list((packages / "python").glob("*.whl"))
    sdists = list((packages / "python").glob("*.tar.gz"))
    assert len(wheels) == len(sdists) == 1, "Expected one wheel and one sdist"
    with zipfile.ZipFile(wheels[0]) as wheel:
        metadata_paths = [
            name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")
        ]
        assert len(metadata_paths) == 1
        metadata = email.message_from_bytes(wheel.read(metadata_paths[0]))
        assert metadata["Name"] == project["name"] and metadata["Version"] == version
        for package in ("openai_mcp_extensions", "openai_mcp_form_protocol"):
            assert f"{package}/__init__.py" in wheel.namelist(), f"Missing {package}"
    with tarfile.open(sdists[0]) as sdist:
        metadata_paths = [name for name in sdist.getnames() if name.count("/") == 1]
        metadata_path = next(
            name for name in metadata_paths if name.endswith("/PKG-INFO")
        )
        stream = sdist.extractfile(metadata_path)
        assert stream is not None
        metadata = email.message_from_bytes(stream.read())
        assert metadata["Name"] == project["name"] and metadata["Version"] == version
    with tarfile.open(packages / "node/package.tgz") as archive:
        stream = archive.extractfile("package/package.json")
        assert stream is not None
        packed = json.load(stream)
        assert packed["name"] == node["name"] and packed["version"] == node_version
        assert not packed.get("private")
        for export in packed["exports"].values():
            paths = export.values() if isinstance(export, dict) else [export]
            for path in paths:
                assert f"package/{path.removeprefix('./')}" in archive.getnames(), path
        assert "package/LICENSE" in archive.getnames()
    print(f"Validated Python {version} wheel/sdist and Node {node_version} tarball")


if __name__ == "__main__":
    check(Path(sys.argv[1]))
