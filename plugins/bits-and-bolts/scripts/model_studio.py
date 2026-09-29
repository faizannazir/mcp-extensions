"""Editable surface finishes and product lighting for the Codex Micro scene."""

import math

import bpy
from mathutils import Vector


def material(name, color, metallic=0, roughness=0.35, transmission=0, grain=0, relief=0):
    finish = bpy.data.materials.new(name)
    finish.diffuse_color = (*color, 1)
    finish.use_nodes = True
    nodes, links = finish.node_tree.nodes, finish.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Transmission Weight"].default_value = transmission
    shader.inputs["IOR"].default_value = 1.585 if transmission else 1.5
    if grain:
        coordinates = nodes.new("ShaderNodeTexCoord")
        coordinates.location = (-760, 0)
        noise = nodes.new("ShaderNodeTexNoise")
        noise.label = "Fine manufacturing finish (model units are millimeters)"
        noise.location = (-540, 0)
        noise.inputs["Scale"].default_value = grain
        noise.inputs["Detail"].default_value = 2
        noise.inputs["Roughness"].default_value = 0.65
        links.new(coordinates.outputs["Object"], noise.inputs["Vector"])
        variation = nodes.new("ShaderNodeMapRange")
        variation.location = (-280, 80)
        variation.inputs["To Min"].default_value = roughness - 0.035
        variation.inputs["To Max"].default_value = roughness + 0.035
        links.new(noise.outputs["Fac"], variation.inputs["Value"])
        links.new(variation.outputs["Result"], shader.inputs["Roughness"])
        bump = nodes.new("ShaderNodeBump")
        bump.location = (-280, -170)
        bump.inputs["Strength"].default_value = 0.18
        bump.inputs["Distance"].default_value = relief
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return finish


def finish_surfaces(objects):
    for obj in objects:
        if obj.type != "MESH":
            continue
        # Planar caps stay planar; rounded profiles remain smooth between creases.
        for face in obj.data.polygons:
            face.use_smooth = len(face.vertices) <= 4 and abs(face.normal.z) < 0.9999
        obj.data.set_sharp_from_angle(angle=math.radians(45))
        if obj.get("keycap_units"):
            keycap_normals(obj)
        if obj.get("sculpted_dial"):
            dial_normals(obj)
        if obj.data.materials and obj.data.materials[0].name == "Printed graphite ink":
            continue
        # These editable highlights do not inflate the portable STL mesh budget.
        bevel = obj.modifiers.new("Manufactured edge highlights", "BEVEL")
        bevel.width = 0.045
        bevel.segments = 3
        bevel.limit_method = "ANGLE"
        bevel.angle_limit = math.radians(55)
        bevel.harden_normals = True


def keycap_normals(obj):
    """Keep molded dishes and planar rims independent of Boolean triangulation."""
    mesh = obj.data
    extra = (obj["keycap_units"] - 1) * 19.05
    square = obj["square_dish"]
    normals = [normal.vector.copy() for normal in mesh.corner_normals]
    for face in mesh.polygons:
        for index in face.loop_indices:
            point = mesh.vertices[mesh.loops[index].vertex_index].co
            x, y = max(0, abs(point.x) - extra / 2), abs(point.y)
            if square:
                radius = max(x, y)
                dx, dy = (1, 0) if x >= y else (0, 1)
                if min(x, y) > 0.6 * radius:
                    # Level sets are rounded squares with a corner radius of 0.4r.
                    radius = (
                        1.2 * (x + y) - math.sqrt(1.44 * (x + y) ** 2 - 2.24 * (x * x + y * y))
                    ) / 1.12
                    denominator = 1.2 * (x + y) - 1.12 * radius
                    dx = (2 * x - 1.2 * radius) / denominator
                    dy = (2 * y - 1.2 * radius) / denominator
            else:
                radius = math.hypot(x, y)
                dx, dy = (x / radius, y / radius) if radius else (0, 0)
            if (
                face.center.z > (4.45 if square else 3.6)
                and face.normal.z > 0.2
                and (not square or radius < 7.85)
            ):
                if square:
                    slope = 1.9 * radius / 7.2**2
                    if radius > 7.2:
                        slope *= max(0, (7.6 - radius) / 0.4)
                else:
                    # Flat rim polygons need the same loop normals as adjoining quads.
                    face.use_smooth = True
                    slope = 3.5 * min(radius, 6.6) / 6.6**2
                    if radius > 6.6:
                        slope *= max(0, (7.25 - radius) / 0.65)
                normals[index] = Vector(
                    (-slope * math.copysign(dx, point.x), -slope * math.copysign(dy, point.y), 1)
                ).normalized()
            elif max(abs(face.center.x) - extra / 2, abs(face.center.y)) > 7.7:
                if not square:
                    face.use_smooth = True
                normal = Vector(
                    (
                        point.x - max(-6 - extra / 2, min(6 + extra / 2, point.x)),
                        point.y - max(-6, min(6, point.y)),
                        0,
                    )
                ).normalized()
                angle = max(0, min(1, (point.z - 5.15) / 0.4)) * math.pi / 2
                normal *= math.cos(angle)
                normal.z = math.sin(angle)
                normals[index] = normal
            elif (
                face.center.z < 2.75
                and face.normal.dot(Vector((face.center.x, face.center.y, 0))) < -1
            ):
                normal = Vector(
                    (
                        point.x - max(-5.1 - extra / 2, min(5.1 + extra / 2, point.x)),
                        point.y - max(-5.1, min(5.1, point.y)),
                        0,
                    )
                )
                if normal.length:
                    normals[index] = -normal.normalized()
    mesh.normals_split_custom_set(normals)


def dial_normals(obj):
    mesh = obj.data
    normals = [normal.vector.copy() for normal in mesh.corner_normals]
    for face in mesh.polygons:
        outer_wall = math.hypot(face.center.x, face.center.y) > 8.5
        if face.center.z < 0.75 or (not outer_wall and face.center.z < 6.6):
            continue
        for index in face.loop_indices:
            point = mesh.vertices[mesh.loops[index].vertex_index].co
            if outer_wall:
                normals[index] = Vector((point.x, point.y, 0)).normalized()
            elif face.center.y >= 0:
                normals[index] = Vector((0, 0, 1))
            else:
                y = point.y + 5.5
                normals[index] = Vector((0, -y, math.sqrt(max(0, 5.5**2 - y**2)))).normalized()
    mesh.normals_split_custom_set(normals)


def studio(preview=False):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48 if preview else 192
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.012
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 12
    scene.cycles.transmission_bounces = 8
    scene.render.resolution_x = 1000 if preview else 2048
    scene.render.resolution_y = scene.render.resolution_x
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.15
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.82, 0.87, 1, 1)
    background.inputs["Strength"].default_value = 0.055
    bpy.ops.mesh.primitive_plane_add(size=1200, location=(0, 0, -0.025))
    floor = bpy.context.object
    floor.name = "Studio floor"
    floor.data.materials.append(
        material("Neutral seamless backdrop", (0.55, 0.575, 0.60), roughness=0.8)
    )
    for name, position, power, width, height in [
        ("Key softbox", (-120, -160, 180), 700000, 70, 95),
        ("Soft fill", (140, -40, 100), 75000, 120, 100),
        ("Rim softbox", (-90, 130, 150), 210000, 70, 110),
        ("Edge strip", (-135, 55, 50), 40000, 22, 70),
    ]:
        light = bpy.data.lights.new(name, "AREA")
        light.energy, light.shape = power, "RECTANGLE"
        light.size, light.size_y = width, height
        obj = bpy.data.objects.new(name, light)
        scene.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (Vector((0, 0, 8)) - obj.location).to_track_quat("-Z", "Y").to_euler()
    camera = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.lens = 65
    camera.data.clip_start = 0.1
    camera.data.clip_end = 2000
    return camera, floor
