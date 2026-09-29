"""Portable display companions with baked, shared manufacturing finishes."""

import bpy
from mathutils import Matrix


def export_models(parts, output, local):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 1
    scene.render.bake.use_selected_to_active = False
    textures = local / "glb-textures"
    textures.mkdir(exist_ok=True)
    materials = {
        material for objects in parts.values() for obj in objects for material in obj.data.materials
    }
    finishes = {
        source: portable_finish(source, textures)
        for source in sorted(materials, key=lambda material: material.name)
    }
    graph = bpy.context.evaluated_depsgraph_get()
    for filename, objects in parts.items():
        bpy.ops.object.select_all(action="DESELECT")
        copies = []
        for obj in objects:
            evaluated = obj.evaluated_get(graph)
            mesh = bpy.data.meshes.new_from_object(
                evaluated, preserve_all_data_layers=True, depsgraph=graph
            )
            if not mesh.polygons:
                raise ValueError(f"Cannot export an empty display mesh: {obj.name}")
            display = bpy.data.objects.new(obj.name + " display", mesh)
            bpy.context.collection.objects.link(display)
            # glTF is Y-up meters; Blender's scene display units do not scale exports.
            display.matrix_world = Matrix.Scale(0.001, 4) @ obj.matrix_world
            for index, material in enumerate(mesh.materials):
                mesh.materials[index] = finishes[material]
            uv = mesh.uv_layers.new(name="Surface")
            diffuser = obj.name == "Diffused perimeter lighting"
            for face in mesh.polygons:
                axis = max(range(3), key=lambda index: abs(face.normal[index]))
                a, b = ((1, 2), (0, 2), (0, 1))[axis]
                for index in face.loop_indices:
                    point = mesh.vertices[mesh.loops[index].vertex_index].co
                    uv.data[index].uv = (
                        (0.5, (point.y + 51.5) / 103) if diffuser else (point[a] / 4, point[b] / 4)
                    )
            display.select_set(True)
            copies.append(display)
        target = output / filename
        bpy.ops.export_scene.gltf(
            filepath=str(target),
            export_format="GLB",
            use_selection=True,
            export_yup=True,
            export_normals=True,
            export_texcoords=True,
            export_cameras=False,
            export_lights=False,
            export_animations=False,
            export_extras=False,
        )
        for obj in copies:
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.meshes.remove(mesh)
        if target.stat().st_size > 7 * 1024 * 1024:
            raise ValueError(f"GLB exceeds the MCP transport budget: {filename}")
        print(filename, target.stat().st_size, "bytes", flush=True)


def portable_finish(source, directory):
    finish = bpy.data.materials.new(source.name + " display")
    finish.use_nodes = True
    finish.use_backface_culling = True
    shader = finish.node_tree.nodes.get("Principled BSDF")
    original = source.node_tree.nodes.get("Principled BSDF")
    for name in (
        "Base Color",
        "Metallic",
        "Roughness",
        "IOR",
        "Transmission Weight",
        "Emission Color",
        "Emission Strength",
    ):
        shader.inputs[name].default_value = original.inputs[name].default_value
    if any(node.type == "TEX_NOISE" for node in source.node_tree.nodes):
        bpy.ops.mesh.primitive_plane_add(size=4)
        plane = bpy.context.object
        baking = source.copy()
        plane.data.materials.append(baking)
        for kind in ("NORMAL", "ROUGHNESS"):
            image = bpy.data.images.new(source.name + " " + kind.lower(), 256, 256)
            image.colorspace_settings.name = "Non-Color"
            target = baking.node_tree.nodes.new("ShaderNodeTexImage")
            target.image = image
            baking.node_tree.nodes.active = target
            bpy.ops.object.bake(type=kind, margin=0)
            image.filepath_raw = str(directory / (image.name.lower().replace(" ", "-") + ".png"))
            image.file_format = "PNG"
            image.save()
            image.pack()
            texture = finish.node_tree.nodes.new("ShaderNodeTexImage")
            texture.image = image
            if kind == "NORMAL":
                normal = finish.node_tree.nodes.new("ShaderNodeNormalMap")
                finish.node_tree.links.new(texture.outputs["Color"], normal.inputs["Color"])
                finish.node_tree.links.new(normal.outputs["Normal"], shader.inputs["Normal"])
            else:
                finish.node_tree.links.new(texture.outputs["Color"], shader.inputs["Roughness"])
        mesh = plane.data
        bpy.data.objects.remove(plane, do_unlink=True)
        bpy.data.meshes.remove(mesh)
        bpy.data.materials.remove(baking)
    if source.name == "Mint and lavender internal diffuser":
        image = bpy.data.images.new("Mint and lavender diffuser", 4, 64)
        ramp = next(node.color_ramp for node in source.node_tree.nodes if node.type == "VALTORGB")
        image.pixels.foreach_set(
            [value for y in range(64) for _ in range(4) for value in ramp.evaluate(y / 63)]
        )
        image.pack()
        texture = finish.node_tree.nodes.new("ShaderNodeTexImage")
        texture.image = image
        texture.extension = "EXTEND"
        finish.node_tree.links.new(texture.outputs["Color"], shader.inputs["Emission Color"])
    return finish
