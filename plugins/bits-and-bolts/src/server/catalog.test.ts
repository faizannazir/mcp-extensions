import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, unlink, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";

import seeds from "../../assets/models/catalog.json" with { type: "json" };
import type { CadPart } from "./catalog.js";
import legacyKeycap from "./fixtures/legacy-command-keycap.stl";

test("bundled models migrate without replacing edited or imported parts", async () => {
  const directory = await mkdtemp(
    path.join(os.tmpdir(), "bits-and-bolts-catalog-"),
  );
  process.env.CAD_LIBRARY_HOME = directory;
  try {
    const { initializeCatalog, importPart, readPartBytes, savePartPreviews } =
      await import("./catalog.js");
    const fresh = await initializeCatalog();
    assert.equal(fresh.length, seeds.length);
    for (const seed of seeds) {
      const { bytes, format } = await readPartBytes(seed.id);
      assert.equal(format, "stl");
      assert.ok(
        bytes.length < 7 * 1024 * 1024,
        "base64 model must fit the MCP transport",
      );
      assert.deepEqual(
        bytes,
        await readFile(
          new URL(`../assets/models/${seed.assetPath}`, import.meta.url),
        ),
      );
      const display = await readPartBytes(seed.id, "display");
      assert.equal(display.format, "glb");
      assert.equal(display.part.format, "stl");
      assert.ok(
        display.bytes.length < 7 * 1024 * 1024,
        "base64 display model must fit the MCP transport",
      );
      const displayPath = path.posix.join(
        path.posix.dirname(seed.assetPath),
        `${path.posix.parse(seed.assetPath).name}.glb`,
      );
      assert.deepEqual(
        display.bytes,
        await readFile(
          new URL(`../assets/models/${displayPath}`, import.meta.url),
        ),
      );
    }

    const keycap = fresh.find((part) => part.id === "part_command_keycap");
    const assembly = fresh.find((part) => part.id === "part_micro_controller");
    const dial = fresh.find((part) => part.id === "part_agent_dial");
    assert.ok(keycap && assembly && dial);
    await savePartPreviews(keycap.id, { top: "data:image/png;base64,preview" });
    // The dial already has new bytes, as after an interrupted migration.
    await savePartPreviews(dial.id, { top: "data:image/png;base64,stale" });
    const edited = Buffer.from(
      legacyKeycap.replace("Command_keycap", "User_edited_assembly"),
    );
    await writeFile(assembly.storagePath, edited);
    const imported = await importPart({
      bytes: edited,
      fileName: "custom.stl",
      name: "My part",
    });
    for (const part of [assembly, imported]) {
      const display = await readPartBytes(part.id, "display");
      assert.equal(display.format, "stl");
      assert.deepEqual(display.bytes, edited);
    }

    const manifestPath = path.join(directory, "catalog.json");
    const original = JSON.parse(await readFile(manifestPath, "utf8"));
    original.parts = original.parts.filter((part: CadPart) =>
      [
        "part_command_keycap",
        "part_micro_controller",
        "part_agent_dial",
        imported.id,
      ].includes(part.id),
    );
    for (const bundledModelVersion of [undefined, 1, 2, 3, 4, 5]) {
      await writeFile(keycap.storagePath, legacyKeycap);
      await writeFile(
        manifestPath,
        JSON.stringify({ ...original, bundledModelVersion }),
      );
      const migrated = await initializeCatalog();
      assert.equal(migrated.length, seeds.length + 1);
      const updated = await readPartBytes(keycap.id);
      assert.deepEqual(
        updated.bytes,
        await readFile(
          new URL("../assets/models/keycaps/codex.stl", import.meta.url),
        ),
      );
      assert.deepEqual(updated.part.previews, {});
      assert.deepEqual((await readPartBytes(dial.id)).part.previews, {});
      assert.deepEqual((await readPartBytes(assembly.id)).bytes, edited);
      assert.deepEqual((await readPartBytes(imported.id)).part, imported);
    }

    const afterMigration = await readFile(manifestPath, "utf8");
    await initializeCatalog();
    assert.equal(await readFile(manifestPath, "utf8"), afterMigration);

    const missing = JSON.parse(afterMigration);
    missing.bundledModelVersion = 0;
    await unlink(keycap.storagePath);
    await writeFile(manifestPath, JSON.stringify(missing));
    await initializeCatalog();
    await assert.rejects(readFile(keycap.storagePath), { code: "ENOENT" });
    await assert.rejects(readPartBytes(keycap.id, "display"), {
      message: `The source file for ${keycap.name} is missing.`,
    });

    await writeFile(manifestPath, "broken catalog");
    await assert.rejects(initializeCatalog(), SyntaxError);
    assert.equal(await readFile(manifestPath, "utf8"), "broken catalog");
  } finally {
    delete process.env.CAD_LIBRARY_HOME;
    await rm(directory, { recursive: true, force: true });
  }
});
