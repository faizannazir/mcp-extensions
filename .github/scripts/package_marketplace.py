"""Package the built marketplace without source dependencies."""

import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[2]
manifest = root / ".agents/plugins/marketplace.json"
marketplace = json.loads(manifest.read_text())
files = [manifest, root / "LICENSE"]

for entry in marketplace["plugins"]:
    source = entry["source"]
    if source["source"] != "local":
        raise ValueError(f"Expected a local plugin source: {entry['name']}")
    plugin = (root / source["path"]).resolve()
    plugin.relative_to(root)
    # These are the runtime files used by the example plugins.
    for name in (
        ".codex-plugin",
        ".mcp.json",
        "assets",
        "dist",
        "package.json",
        "skills",
    ):
        path = plugin / name
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}; run pnpm build first")
        if path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
        else:
            files.append(path)

output = Path(sys.argv[1])
output.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
    for path in sorted(files):
        name = f"{marketplace['name']}/{path.relative_to(root).as_posix()}"
        archive.write(path, name)

print(output)
