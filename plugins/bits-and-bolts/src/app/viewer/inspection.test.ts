import assert from "node:assert/strict";
import { test } from "node:test";

import {
  Box3,
  BoxGeometry,
  Group,
  Mesh,
  MeshPhysicalMaterial,
  MeshStandardMaterial,
  PerspectiveCamera,
  SphereGeometry,
  Texture,
  Vector3,
} from "three";
import { STLExporter } from "three/addons/exporters/STLExporter.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

import { disposeObjectResources, parseMeshModel } from "../shared/model.js";
import { parseStl } from "../shared/stl.js";
import {
  fitCamera,
  getMeshBounds,
  setCameraPreset,
  type ViewPreset,
} from "./inspection.js";

test("camera presets fit all bounds in wide and narrow viewports", () => {
  const bounds = new Box3(new Vector3(-54, -54, -4), new Vector3(54, 54, 27));
  for (const aspect of [0.25, 1, 2.5]) {
    for (const preset of [
      "isometric",
      "front",
      "back",
      "left",
      "right",
      "top",
      "bottom",
    ] satisfies ViewPreset[]) {
      const camera = new PerspectiveCamera(42, aspect, 0.01, 100000);
      camera.position.set(100, -100, 100);
      const target = new Vector3();
      setCameraPreset(camera, target, preset);
      fitCamera(camera, target, bounds);
      assert.deepEqual(
        target.toArray(),
        bounds.getCenter(new Vector3()).toArray(),
      );
      for (const x of [bounds.min.x, bounds.max.x]) {
        for (const y of [bounds.min.y, bounds.max.y]) {
          for (const z of [bounds.min.z, bounds.max.z]) {
            const projected = new Vector3(x, y, z).project(camera);
            assert(
              Math.abs(projected.x) < 1 &&
                Math.abs(projected.y) < 1 &&
                Math.abs(projected.z) < 1,
              `${preset} at aspect ${aspect} clips the model`,
            );
          }
        }
      }
      const firstFit = camera.position.clone();
      fitCamera(camera, target, bounds);
      assert(
        firstFit.distanceTo(camera.position) < 1e-9,
        "Repeated fit must not move the camera",
      );
    }
  }
});

test("dimensions follow model transforms but exclude viewer annotations", () => {
  const root = new Group();
  const mesh = new Mesh(new BoxGeometry(10, 20, 30));
  root.add(mesh);
  const annotation = new Mesh(new BoxGeometry(100, 100, 100));
  mesh.add(annotation);
  root.rotateX(Math.PI / 2);
  root.position.set(5, 10, 15);
  const bounds = getMeshBounds([mesh]);
  const size = bounds.getSize(new Vector3());
  assert(Math.abs(size.x - 10) < 1e-9);
  assert(Math.abs(size.y - 30) < 1e-9);
  assert(Math.abs(size.z - 20) < 1e-9);
  assert.deepEqual(bounds.getCenter(new Vector3()).toArray(), [5, 10, 15]);
});

test("STL smoothing is scale-independent and preserves CAD coordinates", () => {
  let expectedNormals: Float32Array | null = null;
  for (const scale of [1, 0.000001, 1000000]) {
    const mesh = new Mesh(new SphereGeometry(scale, 12, 6));
    mesh.position.set(2 * scale, -3 * scale, 4 * scale);
    mesh.updateMatrixWorld(true);
    const exported = new STLExporter().parse(mesh, { binary: true });
    assert(exported instanceof DataView);
    const bytes = new Uint8Array(
      exported.buffer,
      exported.byteOffset,
      exported.byteLength,
    ).slice();
    const originalBytes = bytes.slice();
    const original = new STLLoader().parse(bytes.buffer);
    const smoothed = parseStl(bytes.buffer);
    assert.deepEqual(bytes, originalBytes);
    assert.deepEqual(
      smoothed.getAttribute("position").array,
      original.getAttribute("position").array,
    );
    const normals = new Float32Array(smoothed.getAttribute("normal").array);
    assert.notDeepEqual(normals, original.getAttribute("normal").array);
    if (expectedNormals == null) {
      expectedNormals = normals;
    } else {
      for (let index = 0; index < normals.length; index++) {
        assert(Math.abs(normals[index] - expectedNormals[index]) < 0.00001);
      }
    }
    original.dispose();
    smoothed.dispose();
    mesh.geometry.dispose();
  }
});

test("GLB display converts meters to Z-up mm and keeps authored PBR attributes", async (context) => {
  const positions = new Float32Array([0, 0, 0, 0.02, 0, 0, 0, 0.03, 0.004]);
  const normals = new Float32Array([0, 0, 1, 0, 0, 1, 0, 0, 1]);
  const uvs = new Float32Array([0, 0, 1, 0, 0, 1]);
  const binary = new Float32Array([...positions, ...normals, ...uvs]);
  const json = new TextEncoder().encode(
    JSON.stringify({
      asset: { version: "2.0" },
      scene: 0,
      scenes: [{ nodes: [0] }],
      nodes: [{ mesh: 0 }],
      meshes: [
        {
          primitives: [
            {
              attributes: { POSITION: 0, NORMAL: 1, TEXCOORD_0: 2 },
              material: 0,
            },
          ],
        },
      ],
      buffers: [{ byteLength: binary.byteLength }],
      bufferViews: [
        { buffer: 0, byteOffset: 0, byteLength: positions.byteLength },
        {
          buffer: 0,
          byteOffset: positions.byteLength,
          byteLength: normals.byteLength,
        },
        {
          buffer: 0,
          byteOffset: positions.byteLength + normals.byteLength,
          byteLength: uvs.byteLength,
        },
      ],
      accessors: [
        {
          bufferView: 0,
          componentType: 5126,
          count: 3,
          type: "VEC3",
          min: [0, 0, 0],
          max: [0.02, 0.03, 0.004],
        },
        { bufferView: 1, componentType: 5126, count: 3, type: "VEC3" },
        { bufferView: 2, componentType: 5126, count: 3, type: "VEC2" },
      ],
      extensionsUsed: ["KHR_materials_transmission", "KHR_materials_volume"],
      materials: [
        {
          alphaMode: "BLEND",
          pbrMetallicRoughness: {
            baseColorFactor: [0.2, 0.4, 0.6, 0.65],
            metallicFactor: 0.4,
            roughnessFactor: 0.3,
          },
          extensions: {
            KHR_materials_transmission: { transmissionFactor: 0.5 },
            KHR_materials_volume: {
              thicknessFactor: 0.001,
              attenuationDistance: 0.01,
            },
          },
        },
      ],
    }),
  );
  const jsonLength = Math.ceil(json.length / 4) * 4;
  const bytes = new ArrayBuffer(28 + jsonLength + binary.byteLength);
  const header = new DataView(bytes);
  for (const [offset, value] of [
    [0, 0x46546c67],
    [4, 2],
    [8, bytes.byteLength],
    [12, jsonLength],
    [16, 0x4e4f534a],
    [20 + jsonLength, binary.byteLength],
    [24 + jsonLength, 0x004e4942],
  ])
    header.setUint32(offset, value, true);
  new Uint8Array(bytes, 20, jsonLength).fill(32);
  new Uint8Array(bytes, 20, json.length).set(json);
  new Float32Array(bytes, 28 + jsonLength).set(binary);

  const model = await parseMeshModel("glb", bytes);
  context.after(() => disposeObjectResources(model));
  const mesh = model.getObjectByProperty("isMesh", true);
  assert(mesh instanceof Mesh);
  const bounds = getMeshBounds([mesh]);
  assert(bounds.min.distanceTo(new Vector3(0, -4, 0)) < 0.00001);
  assert(bounds.max.distanceTo(new Vector3(20, 0, 30)) < 0.00001);
  const selectedPoint = model.worldToLocal(
    mesh.localToWorld(new Vector3(0, 0.03, 0.004)),
  );
  assert(selectedPoint.distanceTo(new Vector3(0, -4, 30)) < 0.00001);
  assert.equal(model.userData.lengthUnit, "mm");
  assert.deepEqual(mesh.geometry.getAttribute("position").array, positions);
  assert.deepEqual(mesh.geometry.getAttribute("normal").array, normals);
  assert.deepEqual(mesh.geometry.getAttribute("uv").array, uvs);
  assert(mesh.material instanceof MeshPhysicalMaterial);
  assert.deepEqual(mesh.material.color.toArray(), [0.2, 0.4, 0.6]);
  assert.equal(mesh.material.opacity, 0.65);
  assert.equal(mesh.material.transparent, true);
  assert.equal(mesh.material.metalness, 0.4);
  assert.equal(mesh.material.roughness, 0.3);
  assert.equal(mesh.material.transmission, 0.5);
  assert.equal(mesh.material.thickness, 0.001);
  assert.equal(mesh.material.attenuationDistance, 10);
});

test("model cleanup releases shared mesh and texture resources once", () => {
  const geometry = new BoxGeometry();
  const texture = new Texture();
  const plastic = new MeshStandardMaterial({ map: texture });
  const glass = new MeshPhysicalMaterial({
    map: texture,
    roughnessMap: texture,
  });
  const model = new Group();
  model.add(new Mesh(geometry, [plastic, glass]), new Mesh(geometry, plastic));
  const disposed: string[] = [];
  geometry.addEventListener("dispose", () => disposed.push("geometry"));
  texture.addEventListener("dispose", () => disposed.push("texture"));
  plastic.addEventListener("dispose", () => disposed.push("plastic"));
  glass.addEventListener("dispose", () => disposed.push("glass"));
  disposeObjectResources(model);
  assert.deepEqual(disposed.sort(), [
    "geometry",
    "glass",
    "plastic",
    "texture",
  ]);
});
