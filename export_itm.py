import bpy
import bmesh
import json
from struct import pack


ITM_HEADER_PROP = "itm_header"
ITM_PIVOT_A_PROP = "itm_pivot_a"
ITM_PIVOT_B_PROP = "itm_pivot_b"
ITM_MARKERS_PROP = "itm_markers_json"
ITM_MARKER_ID_PROP = "itm_marker_id"
ITM_MARKER_INDEX_PROP = "itm_marker_index"


def vec3_prop(obj, key, fallback):
    value = obj.get(key)
    if value is None:
        return fallback

    try:
        return (float(value[0]), float(value[1]), float(value[2]))
    except Exception:
        return fallback


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
    vertex_uvs = []
    seen_uvs = []
    faces = []

    for vertex in bm.verts:
        x, z, y = vertex.co[:]
        vertices.append((x, y, z))
        vertex_uvs.append((0.0, 0.0))
        seen_uvs.append(False)

    for face in bm.faces:
        vertex_indices = []
        for loop in face.loops:
            vertex_index = loop.vert.index
            vertex_indices.append(vertex_index)
            if not seen_uvs[vertex_index]:
                uv = loop[uv_layer].uv
                vertex_uvs[vertex_index] = (float(uv.x), float(uv.y))
                seen_uvs[vertex_index] = True
        faces.append(vertex_indices)

    bm.free()
    obj_for_convert.to_mesh_clear()
    return (vertices, vertex_uvs, faces)


def marker_sort_key(obj):
    marker_index = obj.get(ITM_MARKER_INDEX_PROP)
    if isinstance(marker_index, int):
        return (0, marker_index, obj.name)

    return (1, 0, obj.name)


def collect_markers(obj: bpy.types.Object, pivot_a):
    markers = []
    for child in sorted(obj.children, key=marker_sort_key):
        if ITM_MARKER_ID_PROP not in child:
            continue

        marker_id = int(child[ITM_MARKER_ID_PROP])
        x, z, y = child.matrix_local.to_translation()
        markers.append((marker_id, (x + pivot_a[0], y + pivot_a[1], z + pivot_a[2])))

    if markers:
        return markers

    markers_json = obj.get(ITM_MARKERS_PROP)
    if markers_json is None:
        return markers

    try:
        parsed = json.loads(markers_json)
    except Exception:
        return markers

    for entry in parsed:
        marker_id = int(entry["id"])
        x, z, y = entry["pos"]
        markers.append(
            (
                marker_id,
                (float(x) + pivot_a[0], float(y) + pivot_a[1], float(z) + pivot_a[2]),
            )
        )

    return markers


def save(context: bpy.types.Context, filepath: str):
    if bpy.context.active_object is not None:
        bpy.ops.object.mode_set(mode="OBJECT")

    obj = bpy.context.active_object
    if obj is None or obj.type != "MESH":
        return [True, "Select an ITM mesh object"]

    depsgraph = context.evaluated_depsgraph_get()
    data = mesh_to_vertices_faces(obj, depsgraph)
    if data is None:
        return [True, "Failed to evaluate mesh data for export"]

    vertices, vertex_uvs, faces = data
    header = int(obj.get(ITM_HEADER_PROP, 1))
    pivot_a = vec3_prop(obj, ITM_PIVOT_A_PROP, (0.0, 0.0, 0.0))
    pivot_b = vec3_prop(obj, ITM_PIVOT_B_PROP, (0.0, 0.0, 0.0))
    markers = collect_markers(obj, pivot_a)

    with open(filepath, "wb") as f:
        f.write(pack("<I", header & 0xFFFFFFFF))
        f.write(pack("<fff", *pivot_a))
        f.write(pack("<fff", *pivot_b))

        f.write(pack("<i", len(markers)))
        for marker_id, position in markers:
            f.write(pack("<i", int(marker_id)))
            f.write(pack("<fff", *position))

        f.write(pack("<i", len(vertices)))
        for i, vertex in enumerate(vertices):
            x, y, z = vertex
            u, v = vertex_uvs[i]
            f.write(
                pack("<fffff", x + pivot_a[0], y + pivot_a[1], z + pivot_a[2], u, v)
            )

        f.write(pack("<i", len(faces)))
        for face in faces:
            f.write(pack("<i", len(face)))
            for vertex_index in face:
                f.write(pack("<i", vertex_index))

    return [False, None]
