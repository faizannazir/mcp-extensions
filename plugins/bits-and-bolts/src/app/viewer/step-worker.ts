/// <reference lib="webworker" />

import occtImportJs from "occt-import-js";

type StepWorkerRequest = {
  buffer: ArrayBuffer;
  wasmBinary: ArrayBuffer;
};

const workerScope = self as unknown as DedicatedWorkerGlobalScope;

workerScope.addEventListener(
  "message",
  async (event: MessageEvent<StepWorkerRequest>) => {
    try {
      const sourceLengthUnit = detectStepLengthUnit(event.data.buffer);
      const occt = await occtImportJs({
        wasmBinary: new Uint8Array(event.data.wasmBinary),
      });
      const result = occt.ReadStepFile(new Uint8Array(event.data.buffer), {
        linearUnit: "millimeter",
      });
      if (!result.success) {
        workerScope.postMessage({
          success: false,
          error: "OpenCascade could not read this STEP file.",
        });
        return;
      }

      const transferables: Array<ArrayBuffer> = [];
      const meshes = result.meshes.map((sourceMesh) => {
        const position = Float32Array.from(
          sourceMesh.attributes.position.array,
        );
        const normal =
          sourceMesh.attributes.normal == null
            ? undefined
            : Float32Array.from(sourceMesh.attributes.normal.array);
        const index =
          sourceMesh.index == null
            ? undefined
            : Uint32Array.from(sourceMesh.index.array);
        transferables.push(position.buffer);
        if (normal != null) {
          transferables.push(normal.buffer);
        }
        if (index != null) {
          transferables.push(index.buffer);
        }
        return {
          color:
            sourceMesh.color == null ? undefined : Array.from(sourceMesh.color),
          index,
          name: sourceMesh.name,
          normal,
          position,
        };
      });
      workerScope.postMessage(
        { success: true, meshes, sourceLengthUnit },
        transferables,
      );
    } catch (error) {
      workerScope.postMessage({
        success: false,
        error:
          error instanceof Error
            ? error.message
            : "Unable to import this STEP file.",
      });
    }
  },
);

function detectStepLengthUnit(buffer: ArrayBuffer): string | null {
  const text = new TextDecoder().decode(buffer);
  const unitStatements =
    text.match(/#[0-9]+\s*=\s*[^;]*LENGTH_UNIT\s*\(\s*\)[^;]*;/gi) ?? [];
  for (const statement of unitStatements) {
    const conversion = statement.match(
      /CONVERSION_BASED_UNIT\s*\(\s*'([^']+)'/i,
    );
    if (conversion?.[1] != null) {
      const rawUnit = conversion[1].trim();
      const normalizedUnit = rawUnit.toUpperCase().replace(/[\s_-]+/g, " ");
      const conversionUnits: Record<string, string> = {
        CENTIMETER: "cm",
        CENTIMETRE: "cm",
        FOOT: "ft",
        INCH: "in",
        METER: "m",
        METRE: "m",
        MICROMETER: "µm",
        MICROMETRE: "µm",
        MILLIMETER: "mm",
        MILLIMETRE: "mm",
      };
      return conversionUnits[normalizedUnit] ?? rawUnit;
    }
    const siUnit = statement.match(
      /SI_UNIT\s*\(\s*(\$|\.[A-Z_]+\.)\s*,\s*\.METRE\.\s*\)/i,
    );
    if (siUnit?.[1] != null) {
      const siUnits: Record<string, string> = {
        $: "m",
        ".CENTI.": "cm",
        ".DECI.": "dm",
        ".KILO.": "km",
        ".MICRO.": "µm",
        ".MILLI.": "mm",
        ".NANO.": "nm",
      };
      return siUnits[siUnit[1].toUpperCase()] ?? null;
    }
  }
  return null;
}
