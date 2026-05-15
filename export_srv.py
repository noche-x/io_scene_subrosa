import bpy
import bmesh
from struct import pack


def get_base_name(name: str):
    if name.endswith(".collision"):
        return name[: -len(".collision")]

    marker = ".child."
    marker_index = name.find(marker)
    if marker_index >= 0:
        return name[:marker_index]

    return name


def mesh_to_vertices_faces(obj: bpy.types.Object, depsgraph):
    obj_for_convert = obj.evaluated_get(depsgraph)

    try:
        me = obj_for_convert.to_mesh()
    except RuntimeError:
        me = None

    if me is None:
        return None

    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=[face for face in bm.faces if len(face.verts) > 4])
    bm.verts.index_update()

    uv_layer = bm.loops.layers.uv.verify()

    vertices = []
    faces = []

    for vertex in bm.verts:
        vertices.append(vertex.co[:])

    for face in bm.faces:
        vertex_indices = []
        loop_uvs = []
        for loop in face.loops:
            vertex_indices.append(loop.vert.index)
            loop_uvs.append(loop[uv_layer].uv[:])
        faces.append((vertex_indices, loop_uvs))

    bm.free()
    obj_for_convert.to_mesh_clear()
    return (vertices, faces)


def write_mesh_block(f, vertices, faces):
    f.write(pack("<i", len(vertices)))
    for vertex in vertices:
        x, z, y = vertex
        f.write(pack("<fff", x, y, z))

    f.write(pack("<i", len(faces)))
    for vertex_indices, loop_uvs in faces:
        f.write(pack("<i", len(vertex_indices)))
        for i, vertex_index in enumerate(vertex_indices):
            f.write(pack("<i", vertex_index))
            u, v = loop_uvs[i]
            f.write(pack("<ff", u, v))


def get_child_objects(scene: bpy.types.Scene, base_name: str):
    child_prefix = base_name + ".child."
    children = [(0, scene.objects.get(base_name))]
    for obj in scene.objects:
        if obj.type != "MESH" or not obj.name.startswith(child_prefix):
            continue

        index_text = obj.name[len(child_prefix) :]
        try:
            sort_index = int(index_text)
        except ValueError:
            sort_index = 0
        children.append((sort_index + 1, obj))

    children.sort(key=lambda child: child[0])
    return [child[1] for child in children if child[1] is not None]


def get_bounds(meshes):
    all_vertices = []
    for vertices, _ in meshes:
        all_vertices.extend(vertices)

    if len(all_vertices) == 0:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    xs = [vertex[0] for vertex in all_vertices]
    ys = [vertex[2] for vertex in all_vertices]
    zs = [vertex[1] for vertex in all_vertices]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def save_v1(context: bpy.types.Context, filepath: str):
    if bpy.context.active_object is not None:
        bpy.ops.object.mode_set(mode="OBJECT")

    active_object = bpy.context.active_object
    if active_object is None:
        return [True, "Select an SRV mesh object"]

    depsgraph = context.evaluated_depsgraph_get()
    scene = context.scene

    base_name = get_base_name(active_object.name)
    root_object = scene.objects.get(base_name + ".collision")
    if root_object is None or root_object.type != "MESH":
        return [True, "Missing collision mesh: " + base_name + ".collision"]

    render_object = scene.objects.get(base_name)
    if render_object is None or render_object.type != "MESH":
        return [True, "Missing render mesh: " + base_name]

    root_data = mesh_to_vertices_faces(root_object, depsgraph)
    if root_data is None:
        return [True, "Failed to evaluate mesh data for export"]

    child_data = []
    for child in get_child_objects(scene, base_name):
        data = mesh_to_vertices_faces(child, depsgraph)
        if data is not None:
            child_data.append(data)

    with open(filepath, "wb") as f:
        f.write(pack("<i", 1))

        f.write(pack("<i", 1))
        f.write(pack("<ffffff", *get_bounds([root_data] + child_data)))

        f.write(pack("<i", 1))
        write_mesh_block(f, root_data[0], root_data[1])

        f.write(pack("<i", len(child_data)))
        for vertices, faces in child_data:
            write_mesh_block(f, vertices, faces)

    return [False, ""]


def save(context: bpy.types.Context, filepath: str, version: int):
    if version == 1:
        return save_v1(context, filepath)

    return [True, "Unknown .srv file version"]
