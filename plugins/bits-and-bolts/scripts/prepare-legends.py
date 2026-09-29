"""Convert the source SVG fills and strokes into non-overlapping planar meshes.

Use the Python environment described in assets/models/README.md.
"""

import json
import math
from pathlib import Path

from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union
from svgelements import SVG, Shape
from svgelements import Path as SvgPath

ROOT = Path(__file__).resolve().parents[1] / "assets/keycap-legends"


def winding(point, contour):
    x, y = point.x, point.y
    result = 0
    for (ax, ay), (bx, by) in zip(contour, contour[1:] + contour[:1]):
        cross = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
        if ay <= y < by and cross > 0:
            result += 1
        elif by <= y < ay and cross < 0:
            result -= 1
    return result


(ROOT / "meshes").mkdir(exist_ok=True)
for source in sorted(ROOT.glob("*.svg")):
    regions = []
    for element in SVG.parse(str(source), reify=True).elements():
        if not isinstance(element, Shape):
            continue
        contours = []
        for subpath in SvgPath(element).as_subpaths():
            points = []
            for segment in subpath:
                steps = max(1, math.ceil(segment.length() / 0.16))
                points += [
                    (segment.point(i / steps).x, segment.point(i / steps).y) for i in range(steps)
                ]
            end = subpath[-1].end
            points.append((end.x, end.y))
            if len(points) > 2:
                contours.append(points)
        if element.fill.value is not None:
            lines = [LineString(points + [points[0]]) for points in contours]
            for polygon in polygonize(unary_union(lines)):
                count = sum(winding(polygon.representative_point(), points) for points in contours)
                if (
                    (count % 2 != 0)
                    if element.values.get("fill-rule") == "evenodd"
                    else (count != 0)
                ):
                    regions.append(polygon)
        if element.stroke.value is not None:
            regions += [
                LineString(points).buffer(element.stroke_width / 2, quad_segs=8)
                for points in contours
            ]
    # Join point contacts before extrusion; the offset is less than 0.002 mm.
    shape = unary_union(regions).buffer(0.005, quad_segs=2).simplify(0.015, preserve_topology=True)
    if shape.is_empty or not shape.is_valid:
        raise ValueError(f"Invalid legend: {source.name}")
    left, bottom, right, top = shape.bounds
    scale = 4.8 / max(right - left, top - bottom)
    vertices, faces, indices = [], [], {}
    for triangle in constrained_delaunay_triangles(shape).geoms:
        face = []
        for x, y in list(triangle.exterior.coords)[:3]:
            point = (
                round((x - (left + right) / 2) * scale, 6),
                round(((bottom + top) / 2 - y) * scale, 6),
            )
            if point not in indices:
                indices[point] = len(vertices)
                vertices.append(point)
            face.append(indices[point])
        faces.append(face)
    (ROOT / "meshes" / f"{source.stem}.json").write_text(
        json.dumps({"vertices": vertices, "faces": faces}, separators=(",", ":")) + "\n"
    )
    print(source.stem, len(faces), "triangles")
