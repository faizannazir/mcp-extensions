"""Rebuild the photo-referenced Codex Micro meshes with Blender 5.2.

Run Blender --background --python scripts/build-models.py from the plugin.
Dimensions are estimates, not manufacturing specifications. See assets/models/README.md.
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_gltf import export_models
from model_studio import finish_surfaces, material, studio

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets/models"
LOCAL = ROOT / ".local/codex-micro"
LEGENDS = ROOT / "assets/keycap-legends"
PITCH = 19.05
SEGMENTS = 64
MX_CROSS = [
    (-0.625, -2.075),
    (0.625, -2.075),
    (0.625, -0.625),
    (2.075, -0.625),
    (2.075, 0.625),
    (0.625, 0.625),
    (0.625, 2.075),
    (-0.625, 2.075),
    (-0.625, 0.625),
    (-2.075, 0.625),
    (-2.075, -0.625),
    (-0.625, -0.625),
]
GLYPHS = {
    source.stem: json.loads((LEGENDS / "meshes" / f"{source.stem}.json").read_text())
    for source in sorted(LEGENDS.glob("*.svg"))
}


def mesh(name, vertices, faces, finish):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(finish)
    return obj


def outline(width, depth, radius, z, segments=SEGMENTS):
    points = []
    arc_segments = segments // 4
    # Include both tangent points for each arc so the straight sides stay parallel.
    for quadrant, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        x, y = sx * (width / 2 - radius), sy * (depth / 2 - radius)
        for step in range(arc_segments + 1):
            angle = (quadrant + step / arc_segments) * math.pi / 2
            points.append((x + radius * math.cos(angle), y + radius * math.sin(angle), z))
    return points


def loft(name, rings, finish, close=True, caps=False):
    count = len(rings[0])
    faces = []
    for ring in range(len(rings) if close else len(rings) - 1):
        nxt = (ring + 1) % len(rings)
        for i in range(count):
            j = (i + 1) % count
            faces.append((ring * count + i, ring * count + j, nxt * count + j, nxt * count + i))
    if caps:
        faces += [
            tuple(reversed(range(count))),
            tuple((len(rings) - 1) * count + i for i in range(count)),
        ]
    return mesh(name, [point for ring in rings for point in ring], faces, finish)


def rounded_box(name, width, depth, bottom, height, radius, finish, bevel=0.3):
    return loft(
        name,
        [
            outline(width - 2 * bevel, depth - 2 * bevel, max(0.1, radius - bevel), bottom),
            outline(width, depth, radius, bottom + bevel),
            outline(width, depth, radius, bottom + height - bevel),
            outline(
                width - 2 * bevel, depth - 2 * bevel, max(0.1, radius - bevel), bottom + height
            ),
        ],
        finish,
        close=False,
        caps=True,
    )


def lathe(name, profile, finish, segments=SEGMENTS):
    rings = [
        [
            (r * math.cos(i * math.tau / segments), r * math.sin(i * math.tau / segments), z)
            for i in range(segments)
        ]
        for r, z in profile
    ]
    return loft(name, rings, finish, close=False, caps=True)


def boolean(target, cutter, operation="DIFFERENCE"):
    bpy.context.view_layer.objects.active = target
    modifier = target.modifiers.new(operation, "BOOLEAN")
    modifier.operation = operation
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def move(obj, x=0, y=0, z=0):
    obj.location += Vector((x, y, z))
    return obj


def dish_height(x, y, units=1):
    x = max(0, abs(x) - (units - 1) * PITCH / 2)
    radius = min(6.6, math.hypot(x, y))
    return 3.65 + 1.75 * (radius / 6.6) ** 2


def keycap(name, units=1, finish=None, square_dish=False):
    finish = finish or WHITE
    extra = (units - 1) * PITCH
    rings = [
        outline(17.4 + extra, 17.4, 2.7, 0),
        outline(18 + extra, 18, 3.0, 0.35),
        outline(18 + extra, 18, 3.0, 5.15),
        outline(17.9 + extra, 17.9, 2.95, 5.4),
        outline(17.65 + extra, 17.65, 2.9, 5.55),
        outline(15.2 + extra, 15.2, 3.04, 5.55)
        if square_dish
        else outline(14.5 + extra, 14.5, 7.25, 5.55),
        outline(14.8 + extra, 14.8, 2.96, 5.54)
        if square_dish
        else outline(13.8 + extra, 13.8, 6.9, 5.53),
    ]
    for radius in (
        (7.2, 6.65, 5.75, 4.75, 3.5, 1.8, 0.05)
        if square_dish
        else (6.6, 6.1, 5.25, 4.1, 2.8, 1.4, 0.05)
    ):
        width = radius * 2
        height = 4.55 + 0.95 * (radius / 7.2) ** 2 if square_dish else dish_height(radius, 0)
        rings.append(outline(width + extra, width, radius * 0.4 if square_dish else radius, height))
    # The open underside and the female MX socket are modeled, not a solid block.
    cap = loft(name, rings, finish, close=False, caps=True)
    cap["keycap_units"] = units
    cap["square_dish"] = square_dish
    boolean(cap, rounded_box("Underside cavity", 15.2 + extra, 15.2, -1, 3.7, 2.5, finish, 0.25))
    for x in (-PITCH / 2, PITCH / 2) if units == 2 else (0,):
        socket = lathe(name + " socket", [(2.7, 0.25), (2.7, 2.85)], finish, 48)
        boolean(cap, move(socket, x), "UNION")
        recess = loft(
            "Female MX socket",
            [[(px + x, py, z) for px, py in MX_CROSS] for z in (-0.2, 2.55)],
            finish,
            close=False,
            caps=True,
        )
        boolean(cap, recess)
    return cap


def svg_mesh(slug, width=4.8):
    glyph = GLYPHS[slug]
    return mesh(
        slug,
        [(x * width / 4.8, y * width / 4.8, 0) for x, y in glyph["vertices"]],
        glyph["faces"],
        BLACK,
    )


def text_mesh(text, width, name):
    curve = bpy.data.curves.new(name, "FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.resolution_u = 3
    if text in ("yolo", "yeet"):
        curve.font = bpy.data.fonts.load(
            str(Path(bpy.utils.system_resource("DATAFILES", path="fonts")) / "Inter.woff2"),
            check_existing=True,
        )
        curve.shear = 0.16
        curve.resolution_u = 6
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    span = max(v.co.x for v in obj.data.vertices) - min(v.co.x for v in obj.data.vertices)
    scale = width / span
    for vertex in obj.data.vertices:
        vertex.co *= scale
    return obj


def extrude_glyph(flat, height_at, bottom, top, finish):
    bm = bmesh.new()
    bm.from_mesh(flat.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    points = [(v.co.x, v.co.y) for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    boundary = [(e.verts[0].index, e.verts[1].index) for e in bm.edges if e.is_boundary]
    bm.free()
    count = len(points)
    vertices = [(x, y, height_at(x, y) + dz) for dz in (bottom, top) for x, y in points]
    solid_faces = [tuple(reversed(f)) for f in faces] + [tuple(v + count for v in f) for f in faces]
    solid_faces += [(a, b, b + count, a + count) for a, b in boundary]
    return mesh(flat.name + " solid", vertices, solid_faces, finish)


def mark_key(cap, slug, units=1):
    flat = text_mesh(slug, 5.8, slug) if slug in ("yolo", "yeet") else svg_mesh(slug)
    height_at = lambda x, y: dish_height(x, y, units)
    cutter = extrude_glyph(flat, height_at, -0.2, 1.2, BLACK)
    boolean(cap, cutter)
    ink = extrude_glyph(flat, height_at, -0.19, -0.14, INK)
    bpy.data.objects.remove(flat, do_unlink=True)
    return ink


def dial():
    # A half-cylinder finger scoop, not a knurled cylindrical knob.
    segments = 96
    rings = []
    for radius, z in ((7.9, 0), (8.4, 0.3), (8.55, 0.7)):
        rings.append(
            [
                (
                    radius * math.cos(i * math.tau / segments),
                    radius * math.sin(i * math.tau / segments),
                    z,
                )
                for i in range(segments)
            ]
        )
    for radius in [8.55 * (1 - i / 24) for i in range(24)] + [0.01]:
        ring = []
        for i in range(segments):
            x, y = (
                radius * math.cos(i * math.tau / segments),
                radius * math.sin(i * math.tau / segments),
            )
            z = 12.2 if y >= 0 else 12.2 - math.sqrt(max(0, 5.5**2 - (y + 5.5) ** 2))
            ring.append((x, y, z))
        rings.append(ring)
    obj = loft("Sculpted dial", rings, WHITE, close=False, caps=True)
    obj["sculpted_dial"] = True
    boolean(obj, lathe("Encoder bore", [(2.95, -1), (2.95, 4.5)], BLACK, 48))
    obj.rotation_euler.z = math.pi / 4
    return obj


def joystick():
    obj = lathe(
        "Joystick rubber cap",
        [(5.3, 0), (6.0, 0.3), (6.1, 1.2), (5.95, 1.65), (5.3, 1.9), (3.5, 1.55), (0.05, 1.4)],
        RUBBER,
    )
    for angle in (45, 135, 225, 315):
        groove = rounded_box("Diagonal grip", 0.38, 2.5, 1.25, 1, 0.18, BLACK, 0.05)
        a = math.radians(angle)
        groove.rotation_euler.z = -a
        move(groove, 3.55 * math.sin(a), 3.55 * math.cos(a))
        boolean(obj, groove)
    return obj


def duplicate(objects, x, y, z):
    copies = []
    for obj in objects:
        clone = obj.copy()
        clone.data = obj.data.copy()
        bpy.context.collection.objects.link(clone)
        move(clone, x, y, z)
        copies.append(clone)
    return copies


def frame_text(text, width, x, y, angle=0):
    flat = text_mesh(text, width, text)
    ink = extrude_glyph(flat, lambda x, y: 10.35, 0, 0.08, INK)
    bpy.data.objects.remove(flat, do_unlink=True)
    ink.rotation_euler.z = angle
    return move(ink, x, y)


def assembly(keycaps, knob, stick):
    objects = []
    frame = loft(
        "Frosted polycarbonate perimeter",
        [
            outline(105, 105, 11.5, 4),
            outline(108, 108, 13, 5.5),
            outline(108, 108, 13, 9),
            outline(107, 107, 12.5, 10.2),
            outline(104.5, 104.5, 11.5, 10.8),
            outline(95, 95, 6.5, 10.8),
            outline(92, 92, 5, 9.7),
            outline(92, 92, 5, 4),
        ],
        FROST,
    )
    # Rear USB-C opening. This estimated recess is for appearance only.
    usb = rounded_box("USB opening", 10, 4, 5, 3.4, 1.6, BLACK, 0.15)
    move(usb, y=53)
    boolean(frame, usb)
    objects.append(frame)
    objects.append(rounded_box("White circuit plate", 90.8, 90.8, 8.8, 1.5, 4.8, PLATE, 0.15))
    objects.append(
        lathe(
            "Aluminum circular base",
            [(40.8, 0.7), (42.0, 1.5), (42.0, 4.0), (40.8, 4.9)],
            SILVER,
            128,
        )
    )
    objects.append(
        loft(
            "Anti-slip annulus",
            [
                outline(80, 80, 40, 0),
                outline(80, 80, 40, 0.8),
                outline(74, 74, 37, 0.8),
                outline(74, 74, 37, 0),
            ],
            GRIP,
        )
    )
    emblem = svg_mesh("codex", 35)
    objects.append(extrude_glyph(emblem, lambda x, y: 0.1, 0, 0.65, SILVER))
    bpy.data.objects.remove(emblem, do_unlink=True)
    for x in (-39.3, 39.3):
        for y in (-39.3, 39.3):
            screw = lathe(
                "Socket-head fastener",
                [(2.15, 10.2), (2.6, 10.55), (2.6, 12.4), (2.3, 12.7)],
                BLACK,
                40,
            )
            boolean(screw, lathe("Hex socket", [(1.5, 11.6), (1.5, 13.5)], BLACK, 6))
            objects.append(move(screw, x, y))
    for row, columns in ((0, (1, 2)), (1, (0, 1, 2, 3)), (2, (0, 1, 2, 3)), (3, (3,))):
        for column in columns:
            x, y = (column - 1.5) * PITCH, (1.5 - row) * PITCH
            slug = (
                "agent"
                if row < 2
                else ("fast", "approve", "reject", "worktree")[column]
                if row == 2
                else "codex"
            )
            objects += duplicate(keycaps[slug], x, y, 14.0)
            objects.append(
                move(
                    rounded_box(
                        "Low-profile switch",
                        13.5,
                        13.5,
                        10.25,
                        4.0,
                        1.2,
                        SWITCH if row < 2 else BLACK,
                        0.2,
                    ),
                    x,
                    y,
                )
            )
            if row < 2:
                objects.append(
                    move(
                        loft(
                            "Lavender MX stem",
                            [[(px * 0.9, py * 0.9, z) for px, py in MX_CROSS] for z in (13, 16.3)],
                            VIOLET,
                            close=False,
                            caps=True,
                        ),
                        x,
                        y,
                    )
                )
    objects += duplicate(keycaps["microphone"], 0, -1.5 * PITCH, 14)
    for x in (-PITCH / 2, PITCH / 2):
        objects.append(
            move(
                rounded_box("Spacebar switch", 13.5, 13.5, 10.25, 4, 1.2, BLACK, 0.2),
                x,
                -1.5 * PITCH,
            )
        )
    objects += duplicate([knob], -1.5 * PITCH, 1.5 * PITCH, 11.5)
    objects.append(
        move(
            rounded_box("Joystick housing", 17.2, 17.2, 10.3, 5, 2.0, SILVER, 0.3),
            1.5 * PITCH,
            1.5 * PITCH,
        )
    )
    objects += duplicate([stick], 1.5 * PITCH, 1.5 * PITCH, 15.4)
    objects.append(
        move(
            lathe("Touch sensor bezel", [(6.5, 10.2), (6.5, 10.45)], PLATE),
            -1.5 * PITCH,
            -1.5 * PITCH,
        )
    )
    objects.append(
        move(lathe("Touch sensor", [(4, 10.45), (4, 10.55)], BLACK), -1.5 * PITCH, -1.5 * PITCH)
    )
    for dy in (-3.1, 0, 3.1):
        objects.append(
            move(
                rounded_box("Layer indicator", 2.2, 0.85, 10.4, 0.6, 0.2, LED, 0.08),
                -38.3,
                -1.5 * PITCH + dy,
            )
        )
    objects += [
        frame_text("Work Louder | OpenAI 2026", 32, -42, 0, math.pi / 2),
        frame_text("You can just build things", 32, 42, 0, -math.pi / 2),
        frame_text("Let's build", 12, 0, -42),
    ]
    arrow = mesh(
        "Up arrow",
        [
            (-1.5, 0, 0),
            (-1.25, -0.25, 0),
            (-0.18, 0.85, 0),
            (-0.18, -1.6, 0),
            (0.18, -1.6, 0),
            (0.18, 0.85, 0),
            (1.25, -0.25, 0),
            (1.5, 0, 0),
            (0, 1.5, 0),
        ],
        [tuple(range(9))],
        BLACK,
    )
    arrow_ink = extrude_glyph(arrow, lambda x, y: 10.35, 0, 0.08, INK)
    objects.append(move(arrow_ink, 0, 42))
    bpy.data.objects.remove(arrow, do_unlink=True)
    return objects


def export_stl(filename, objects, simplify=False):
    bpy.context.view_layer.update()
    # ASCII preserves portable meshes; the generated files live in blob storage.
    lines = ["solid " + filename.removesuffix(".stl")]
    triangles = 0
    bounds = []
    edges = Counter()
    for obj in objects:
        original = obj
        if simplify and len(obj.data.polygons) > 300:
            obj = obj.copy()
            obj.data = obj.data.copy()
            bpy.context.collection.objects.link(obj)
            bpy.context.view_layer.objects.active = obj
            modifier = obj.modifiers.new("Assembly transport budget", "DECIMATE")
            modifier.ratio = 0.48
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        obj.data.calc_loop_triangles()
        matrix = obj.matrix_world
        for triangle in obj.data.loop_triangles:
            points = [matrix @ obj.data.vertices[i].co for i in triangle.vertices]
            normal = (points[1] - points[0]).cross(points[2] - points[0])
            if normal.length < 1e-14:
                continue
            normal.normalize()
            lines.append("facet normal " + " ".join(f"{v:.6g}" for v in normal))
            lines.append("outer loop")
            for point in points:
                lines.append("vertex " + " ".join(f"{v:.6f}" for v in point))
            vertices = [tuple(round(v, 6) for v in point) for point in points]
            edges.update(tuple(sorted((vertices[i], vertices[(i + 1) % 3]))) for i in range(3))
            lines += ["endloop", "endfacet"]
            triangles += 1
        bounds += [matrix @ Vector(corner) for corner in obj.bound_box]
        if obj != original:
            bpy.data.objects.remove(obj, do_unlink=True)
    lines.append("endsolid")
    if triangles == 0:
        raise ValueError(f"Cannot export an empty model: {filename}")
    if any(count != 2 for count in edges.values()):
        raise ValueError(f"Open or non-manifold edges in {filename}")
    contents = "\n".join(lines) + "\n"
    # cad.readPart returns base64 inside JSON over the SDK's 10 MiB stdio buffer.
    if len(contents.encode()) > 7 * 1024 * 1024:
        raise ValueError(
            f"Model exceeds the MCP transport budget: {filename}, {len(contents.encode())} bytes"
        )
    (OUTPUT / filename).write_text(contents)
    print(filename, triangles, "triangles", flush=True)
    return {
        "triangles": triangles,
        "sizeMm": [
            round(max(p[i] for p in bounds) - min(p[i] for p in bounds), 3) for i in range(3)
        ],
    }


def render(objects, name, location, target, scale):
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            obj.hide_render = obj not in objects and obj.name != "Studio floor"
    camera = bpy.data.objects["Camera"]
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = scale
    bpy.context.scene.render.filepath = str(LOCAL / (name + ".png"))
    bpy.ops.render.render(write_still=True)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "keycaps").mkdir(exist_ok=True)
    LOCAL.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.001
    records, stats, keycaps, display_parts = [], {}, {}, {}
    for entry in json.loads((LEGENDS / "keycaps.json").read_text()):
        slug, units = entry["slug"], entry["units"]
        cap = keycap(entry["name"] + " keycap", units)
        ink = mark_key(cap, slug, units)
        keycaps[slug] = [cap, ink]
        filename = f"keycaps/{slug}.stl"
        stats[filename] = export_stl(filename, [cap])
        display_parts[f"keycaps/{slug}.glb"] = [cap, ink]
        records.append(
            {
                "id": "part_command_keycap"
                if slug == "codex"
                else "part_keycap_" + slug.replace("-", "_"),
                "name": entry["name"] + f" keycap ({units}U)",
                "fileName": "command-keycap.stl" if slug == "codex" else f"keycap-{slug}.stl",
                "assetPath": filename,
                "tags": ["codex-micro", "keycap", f"{units}u", slug],
            }
        )
    agent = keycap("Translucent agent keycap", finish=CLEAR, square_dish=True)
    keycaps["agent"] = [agent]
    knob, stick = dial(), joystick()
    complete = assembly(keycaps, knob, stick)
    for slug, name, filename, objects in [
        ("micro_controller", "Codex Micro assembly", "micro-controller.stl", complete),
        ("agent_dial", "Codex Micro sculpted dial", "agent-dial.stl", [knob]),
        ("joystick", "Codex Micro joystick cap", "joystick-cap.stl", [stick]),
        ("keycap_agent", "Translucent agent keycap (1U)", "keycaps/agent.stl", [agent]),
    ]:
        stats[filename] = export_stl(filename, objects, simplify=slug == "micro_controller")
        display_parts[filename.removesuffix(".stl") + ".glb"] = objects
        records.insert(
            0,
            {
                "id": "part_" + slug,
                "name": name,
                "fileName": "keycap-agent.stl" if slug == "keycap_agent" else filename,
                "assetPath": filename,
                "tags": ["codex-micro", "reference", slug.replace("_", "-")],
            },
        )
    (OUTPUT / "catalog.json").write_text(json.dumps(records, indent=2) + "\n")
    (LOCAL / "mesh-report.json").write_text(json.dumps(stats, indent=2) + "\n")
    # The RGB diffuser is presentation-only; it is not a separate printable shell.
    complete.append(
        loft(
            "Diffused perimeter lighting",
            [
                outline(103, 103, 10.4, 5.7),
                outline(103, 103, 10.4, 6.1),
                outline(102.6, 102.6, 10.2, 6.1),
                outline(102.6, 102.6, 10.2, 5.7),
            ],
            GLOW,
        )
    )
    finish_surfaces(list(bpy.data.objects))
    export_models(display_parts, OUTPUT, LOCAL)
    camera, floor = studio(preview="--preview" in sys.argv)
    spread = []
    for i, entry in enumerate(json.loads((LEGENDS / "keycaps.json").read_text())):
        row, column = divmod(i, 5)
        x = (column - 2) * 24
        if row == 6:
            x = -PITCH if entry["units"] == 2 else PITCH
        spread += duplicate(keycaps[entry["slug"]], x, (3 - row) * 24, 0)
    if "--skip-render" not in sys.argv:
        render(complete, "assembly", (120, -160, 190), (0, 0, 9), 170)
        render(complete, "top", (0, 0, 220), (0, 0, 9), 128)
        render(spread, "keyset", (80, -120, 240), (0, 0, 0), 200)
        render([knob], "dial", (20, -28, 27), (0, 0, 6), 28)
        render(complete, "detail", (90, -110, 130), (-8, 8, 14), 82)
        underside = duplicate(complete, 0, 0, 0)
        flip = Matrix.Translation((0, 0, 23.7)) @ Matrix.Rotation(math.pi, 4, "Y")
        for obj in underside:
            obj.matrix_world = flip @ obj.matrix_world
        render(underside, "underside", (120, -160, 190), (0, 0, 14), 160)
        for obj in underside:
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            obj.hide_render = obj not in complete and obj != floor
            obj.hide_set(obj.hide_render)
    camera.location = (120, -160, 190)
    camera.rotation_euler = (
        (Vector((0, 0, 9)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    camera.data.ortho_scale = 170
    bpy.ops.wm.save_as_mainfile(filepath=str(LOCAL / "codex-micro.blend"))


if __name__ == "__main__":
    WHITE = material(
        "Fine-grain porcelain PBT", (0.78, 0.82, 0.84), roughness=0.43, grain=18, relief=0.004
    )
    BLACK = material(
        "Graphite hardware",
        (0.014, 0.017, 0.02),
        metallic=0.45,
        roughness=0.36,
        grain=24,
        relief=0.002,
    )
    INK = material("Printed graphite ink", (0.006, 0.008, 0.01), roughness=0.52)
    SILVER = material(
        "Sandblasted anodized aluminum",
        (0.78, 0.81, 0.84),
        metallic=1,
        roughness=0.55,
        grain=14,
        relief=0.006,
    )
    PLATE = material(
        "Pearl circuit plate",
        (0.67, 0.72, 0.75),
        metallic=0.25,
        roughness=0.4,
        grain=30,
        relief=0.001,
    )
    CLEAR = material("Clear polycarbonate", (0.87, 0.91, 0.96), roughness=0.2, transmission=0.91)
    FROST = material(
        "Frosted polycarbonate",
        (0.86, 0.91, 0.95),
        roughness=0.29,
        transmission=0.78,
        grain=24,
        relief=0.002,
    )
    RUBBER = material(
        "Matte silicone", (0.013, 0.016, 0.02), roughness=0.78, grain=14, relief=0.009
    )
    GRIP = material(
        "Pearl silicone base grip", (0.68, 0.71, 0.73), roughness=0.86, grain=11, relief=0.025
    )
    SWITCH = material("Satin POM switch housings", (0.24, 0.27, 0.31), roughness=0.42)
    VIOLET = material("Lavender switch stems", (0.28, 0.25, 0.57), roughness=0.4)
    LED = material("Layer indicator lenses", (0.84, 0.88, 0.40), roughness=0.3)
    led_shader = LED.node_tree.nodes.get("Principled BSDF")
    led_shader.inputs["Emission Color"].default_value = (0.88, 0.94, 0.57, 1)
    led_shader.inputs["Emission Strength"].default_value = 0.6
    GLOW = material("Mint and lavender internal diffuser", (0.6, 0.8, 0.78), roughness=0.5)
    glow_nodes, glow_links = GLOW.node_tree.nodes, GLOW.node_tree.links
    coordinates = glow_nodes.new("ShaderNodeTexCoord")
    separate = glow_nodes.new("ShaderNodeSeparateXYZ")
    tint = glow_nodes.new("ShaderNodeValToRGB")
    tint.color_ramp.elements[0].color = (0.16, 0.8, 0.6, 1)
    tint.color_ramp.elements[1].color = (0.42, 0.3, 0.95, 1)
    glow_shader = glow_nodes.get("Principled BSDF")
    glow_shader.inputs["Emission Strength"].default_value = 1.5
    glow_links.new(coordinates.outputs["Generated"], separate.inputs["Vector"])
    glow_links.new(separate.outputs["Y"], tint.inputs["Fac"])
    glow_links.new(tint.outputs["Color"], glow_shader.inputs["Emission Color"])
    main()
