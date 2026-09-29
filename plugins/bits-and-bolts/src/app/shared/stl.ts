import { Box3, BufferGeometry, Vector3 } from "three";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import { toCreasedNormals } from "three/addons/utils/BufferGeometryUtils.js";

/** Smooth STL shading without changing the source geometry or its unit scale. */
export function parseStl(bytes: ArrayBuffer): BufferGeometry {
  const geometry = new STLLoader().parse(bytes);
  const positions = geometry.getAttribute("position");
  const bounds = new Box3().setFromArray(positions.array);
  const size = bounds.getSize(new Vector3());
  const extent = Math.max(size.x, size.y, size.z);
  if (!(extent > 0) || !Number.isFinite(extent)) {
    geometry.computeVertexNormals();
    return geometry;
  }

  // Three.js groups positions at a fixed 0.01 precision. Normalize a copy so
  // unitless, meter-scale STLs do not put every face in the same bucket.
  // https://github.com/mrdoob/three.js/blob/r185/examples/jsm/utils/BufferGeometryUtils.js
  const normalized = new BufferGeometry();
  normalized.setAttribute("position", positions.clone());
  const center = bounds.getCenter(new Vector3());
  normalized.translate(-center.x, -center.y, -center.z);
  const scale = 1000 / extent;
  normalized.scale(scale, scale, scale);
  toCreasedNormals(normalized, Math.PI / 4);
  geometry.setAttribute("normal", normalized.getAttribute("normal"));
  normalized.dispose();
  return geometry;
}
