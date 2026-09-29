/* global URL, clearInterval, console, process, setInterval */

import { readdir, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

let building = false;
let rebuildRequested = false;
let checking = false;

async function rebuild() {
  if (building) {
    rebuildRequested = true;
    return;
  }

  building = true;
  rebuildRequested = false;
  try {
    await import(`./build.mjs?updated=${Date.now()}`);
    console.log(
      `[bits-and-bolts] rebuilt at ${new Date().toLocaleTimeString()}`,
    );
  } catch (error) {
    console.error("[bits-and-bolts] build failed", error);
  } finally {
    building = false;
    if (rebuildRequested) {
      await rebuild();
    }
  }
}

await rebuild();

const sourceRoot = fileURLToPath(new URL("../src", import.meta.url));
let fingerprint = await sourceFingerprint(sourceRoot);
const poller = setInterval(async () => {
  if (checking) {
    return;
  }

  checking = true;
  try {
    const nextFingerprint = await sourceFingerprint(sourceRoot);
    if (nextFingerprint !== fingerprint) {
      fingerprint = nextFingerprint;
      await rebuild();
    }
  } catch (error) {
    console.error("[bits-and-bolts] source scan failed", error);
  } finally {
    checking = false;
  }
}, 500);

console.log("[bits-and-bolts] watching src/ for changes");

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    clearInterval(poller);
    process.exit(0);
  });
}

async function sourceFingerprint(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const fingerprints = await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        return sourceFingerprint(entryPath);
      }
      const metadata = await stat(entryPath);
      return `${entryPath}:${metadata.mtimeMs}:${metadata.size}`;
    }),
  );
  return fingerprints.sort().join("|");
}
