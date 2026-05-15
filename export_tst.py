import bpy
import bmesh
from struct import pack


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


def curve_to_points(obj: bpy.types.Object):
    points = []
    curve = obj.data
    if len(curve.splines) == 0:
        return points

    spline = curve.splines[0]
    for point in spline.points:
        points.append(point.co[:3])

    return points


def get_window_objects(scene: bpy.types.Scene, base_name: str):
    window_prefix = base_name + ".window."
    windows = []
    for obj in scene.objects:
        if obj.type == "CURVE" and obj.name.startswith(window_prefix):
            index_text = obj.name[len(window_prefix) :]
            try:
                sort_index = int(index_text)
            except ValueError:
                sort_index = 0
            windows.append((sort_index, obj))

    windows.sort(key=lambda window: window[0])
    return [window[1] for window in windows]


def write_vertices(f, vertices, with_extra):
    f.write(pack("<i", len(vertices)))
    for vertex in vertices:
        x, z, y = vertex
        f.write(pack("<fff", x, y, z))
        if with_extra:
            f.write(pack("<i", 0))


def write_faces(f, faces, with_tail):
    f.write(pack("<i", len(faces)))
    for vertex_indices, loop_uvs in faces:
        f.write(pack("<i", len(vertex_indices)))
        for i, vertex_index in enumerate(vertex_indices):
            f.write(pack("<i", vertex_index))
            u, v = loop_uvs[i]
            f.write(pack("<ff", u, v))
        if with_tail:
            f.write(pack("<i", 0))


def save_v1(context: bpy.types.Context, filepath: str):
    if bpy.context.active_object is not None:
        bpy.ops.object.mode_set(mode="OBJECT")

    active_object = bpy.context.active_object
    if active_object is None or active_object.type != "MESH":
        return [True, "Select a TST mesh object"]

    depsgraph = context.evaluated_depsgraph_get()
    data = mesh_to_vertices_faces(active_object, depsgraph)
    if data is None:
        return [True, "Failed to evaluate mesh data for export"]

    vertices, faces = data
    windows = get_window_objects(context.scene, active_object.name)

    with open(filepath, "wb") as f:
        f.write(pack("<i", 1))
        write_vertices(f, vertices, False)
        write_faces(f, faces, False)

        f.write(pack("<i", 1))
        f.write(pack("<i", len(windows)))
        for window in windows:
            points = curve_to_points(window)
            f.write(pack("<i", len(points)))
            for point in points:
                x, z, y = point
                f.write(pack("<fff", x, y, z))

    return [False, ""]


def save_v2(context: bpy.types.Context, filepath: str):
    if bpy.context.active_object is not None:
        bpy.ops.object.mode_set(mode="OBJECT")

    active_object = bpy.context.active_object
    if active_object is None or active_object.type != "MESH":
        return [True, "Select a TST mesh object"]

    depsgraph = context.evaluated_depsgraph_get()
    data = mesh_to_vertices_faces(active_object, depsgraph)
    if data is None:
        return [True, "Failed to evaluate mesh data for export"]

    vertices, faces = data

    with open(filepath, "wb") as f:
        f.write(pack("<i", 2))
        f.write(pack("<i", 0))
        write_vertices(f, vertices, True)
        write_faces(f, faces, True)

    return [False, ""]


def save(context: bpy.types.Context, filepath: str, version: int):
    if version == 1:
        return save_v1(context, filepath)
    if version == 2:
        return save_v2(context, filepath)

    return [True, "Unknown .tst file version"]
