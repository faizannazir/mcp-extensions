import type { Group } from "three";
import { Box3, Mesh, Vector3 } from "three";
import { STLExporter } from "three/addons/exporters/STLExporter.js";
import { parseModel } from "../viewer/model.js";
import { mountScene, type SceneApi } from "../viewer/scene.js";
import type { DisplayMode, ViewPreset } from "../viewer/inspection.js";
import type { ModelFormat } from "../../shared/contracts.js";
import type { Renderer, RendererOptions, RenderState } from "./types.js";

export function createRenderer({
  container,
  onChange,
  readWasm,
}: RendererOptions): Renderer {
  let model: Group | null = null;
  let api: SceneApi | null = null;
  let previous: Partial<RenderState> = {};
  let applying = false;
  let selected = false;
  const clear = () => {
    api?.dispose();
    api = null;
    model = null;
    previous = {};
    selected = false;
  };
  function syncCamera() {
    if (!api) return;
    const current = api.getViewerState().camera;
    const [x, y, z] = current.position.map(
      (value, index) => value - current.target[index],
    );
    const actual = {
      camera: current.preset,
      yaw: Math.atan2(x, -y),
      pitch: Math.atan2(z, Math.hypot(x, y)),
      zoom: current.zoom ?? 1,
    };
    if (
      actual.camera !== previous.camera ||
      actual.yaw !== previous.yaw ||
      actual.pitch !== previous.pitch ||
      actual.zoom !== previous.zoom
    ) {
      Object.assign(previous, actual);
      onChange(actual);
    }
  }
  return {
    formats: ["stl", "3mf", "step", "stp"],
    cameras: ["isometric", "front", "top", "right", "back", "left", "bottom"],
    modes: ["solid", "wireframe", "edges", "transparent"],
    async load(source, isCurrent = () => true) {
      if (!source.bytes)
        throw new Error("The CAD resource has no file contents.");
      const next = await parseModel(
        source.format as ModelFormat,
        source.bytes,
        readWasm,
      );
      if (!isCurrent()) {
        next.traverse((object) => {
          if (object instanceof Mesh) {
            object.geometry.dispose();
            for (const material of Array.isArray(object.material)
              ? object.material
              : [object.material])
              material.dispose();
          }
        });
        return;
      }
      clear();
      model = next;
      api = mountScene(
        container,
        model,
        { defaultView: "isometric", units: "mm", showGrid: true },
        (selection) => {
          selected = selection != null;
          onChange({ selection });
        },
      );
      api.subscribe(() => {
        if (!applying) syncCamera();
      });
    },
    draw(next) {
      if (!api) return;
      applying = true;
      try {
        if (next.camera !== previous.camera && next.camera !== "custom")
          api.setView(next.camera as ViewPreset);
        if (
          next.camera === "custom" &&
          (next.yaw !== previous.yaw || next.pitch !== previous.pitch)
        )
          api.setOrbit(next.yaw, next.pitch);
        if (next.mode !== previous.mode)
          api.setDisplay(next.mode as DisplayMode);
        if (next.zoom !== previous.zoom) api.setZoom(next.zoom);
        if (next.grid !== previous.grid) api.setGrid(next.grid);
        if (next.units !== previous.units) api.setUnits(next.units);
        previous = { ...next };
      } finally {
        applying = false;
      }
      syncCamera();
    },
    bounds() {
      if (!model) return { size: [0, 0, 0] };
      return {
        size: new Box3().setFromObject(model).getSize(new Vector3()).toArray(),
      };
    },
    triangleCount() {
      let count = 0;
      model?.traverse((object) => {
        if (object instanceof Mesh)
          count +=
            (object.geometry.index?.count ??
              object.geometry.attributes.position?.count ??
              0) / 3;
      });
      return count;
    },
    fit() {
      api?.fit();
    },
    rotate() {
      selected = false;
      model?.rotateX(Math.PI / 2);
      model?.updateMatrixWorld(true);
      api?.clearSelection();
      api?.fit();
    },
    exportStl() {
      if (!model) throw new Error("Open a model first.");
      const clone = model.clone();
      clone.updateMatrixWorld(true);
      return new STLExporter().parse(clone, { binary: false });
    },
    context() {
      return api?.getViewerState() ?? null;
    },
    capture() {
      if (!api) throw new Error("Open a model first.");
      const url = selected ? api.captureSelection() : api.captureView().dataUrl;
      return {
        data: url.split(",")[1],
        mimeType: url.slice(5, url.indexOf(";")),
      };
    },
    clear,
    clearSelection() {
      selected = false;
      api?.clearSelection();
    },
    dispose: clear,
  };
}
