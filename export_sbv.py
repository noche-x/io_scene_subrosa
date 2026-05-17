import bpy
from struct import pack


FACE_TYPE_UV_TARGETS = (
    (0, 16.5, 0.0),
    (1, 0.0, 1.0),
    (2, 0.09375, 0.09375),
)

FACE_TYPE_MATERIAL_NAMES = (
    "SBV Body",
    "SBV Face Type 1",
    "SBV Face Type 2",
)


def get_base_name(name: str):
    if name.endswith(".collision"):
        return name[: -len(".collision")]
    if name.endswith(".windows"):
        return name[: -len(".windows")]

    markers = (".attachment.", ".wheel.")
    for marker in markers:
        marker_index = name.find(marker)
        if marker_index >= 0:
            return name[:marker_index]

    return name


def infer_face_type_from_uv(mesh: bpy.types.Mesh, polygon: bpy.types.MeshPolygon):
    uv_layer = mesh.uv_layers.active
    if uv_layer is None or len(polygon.loop_indices) == 0:
        return None

    u = 0.0
    v = 0.0
    for loop_index in polygon.loop_indices:
        uv = uv_layer.data[loop_index].uv
        u += uv[0]
        v += uv[1]

    inv_count = 1.0 / len(polygon.loop_indices)
    u *= inv_count
    v *= inv_count

    best_face_type = 0
    best_dist = None
    for face_type, target_u, target_v in FACE_TYPE_UV_TARGETS:
        dist = (u - target_u) * (u - target_u) + (v - target_v) * (v - target_v)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_face_type = face_type

    return best_face_type


def build_face_type_by_material_slot(mesh: bpy.types.Mesh):
    face_type_by_slot = {}

    for material_slot_index, material in enumerate(mesh.materials):
        if material is None:
            continue

        for face_type, material_name in enumerate(FACE_TYPE_MATERIAL_NAMES):
            if material.name == material_name:
                face_type_by_slot[material_slot_index] = face_type
                break

    if len(face_type_by_slot) == 0:
        return None

    return face_type_by_slot


def mesh_to_vertices_faces(
    obj: bpy.types.Object,
    depsgraph,
    reverse_faces: bool,
    face_type_by_material_slot,
):
    obj_for_convert = obj.evaluated_get(depsgraph)

    try:
        me = obj_for_convert.to_mesh()
    except RuntimeError:
        me = None

    if me is None:
        return None

    vertices = []
    faces = []

    for vertex in me.vertices:
        vertices.append(vertex.co[:])

    for polygon in me.polygons:
        vertex_indices = list(polygon.vertices)
        if reverse_faces:
            vertex_indices.reverse()

        if face_type_by_material_slot is None:
            face_type = polygon.material_index
            inferred_face_type = infer_face_type_from_uv(me, polygon)
            if inferred_face_type is not None:
                face_type = inferred_face_type
        else:
            face_type = face_type_by_material_slot.get(
                polygon.material_index,
                polygon.material_index,
            )

        if face_type not in (0, 1, 2):
            face_type = 0

        faces.append((vertex_indices, face_type))

    obj_for_convert.to_mesh_clear()
    return (vertices, faces)


def mesh_to_windows(obj: bpy.types.Object, depsgraph):
    obj_for_convert = obj.evaluated_get(depsgraph)

    try:
        me = obj_for_convert.to_mesh()
    except RuntimeError:
        me = None

    if me is None:
        return []

    windows = []
    for polygon in me.polygons:
        vertex_indices = list(polygon.vertices)
        vertex_indices.reverse()

        window = []
        for vertex_index in vertex_indices:
            window.append(me.vertices[vertex_index].co[:])

        windows.append(window)

    obj_for_convert.to_mesh_clear()
    return windows


def build_edges(faces):
    edge_set = set()

    for face, _ in faces:
        for i in range(len(face)):
            a = face[i]
            b = face[(i + 1) % len(face)]
            edge_set.add((min(a, b), max(a, b)))

    edges = list(edge_set)
    edges.sort()
    return edges


def save(context: bpy.types.Context, filepath: str):
    if bpy.context.active_object is not None:
        bpy.ops.object.mode_set(mode="OBJECT")

    active_object = bpy.context.active_object
    if active_object is None:
        return [True, "Select a vehicle mesh object"]

    depsgraph = context.evaluated_depsgraph_get()
    scene = context.scene

    base_name = get_base_name(active_object.name)
    render_object = scene.objects.get(base_name)
    collision_object = scene.objects.get(base_name + ".collision")
    windows_object = scene.objects.get(base_name + ".windows")

    if render_object is None or render_object.type != "MESH":
        return [True, "Missing render mesh: " + base_name]

    if collision_object is None or collision_object.type != "MESH":
        return [True, "Missing collision mesh: " + base_name + ".collision"]

    render_face_type_by_material_slot = build_face_type_by_material_slot(
        render_object.data
    )
    render_data = mesh_to_vertices_faces(
        render_object,
        depsgraph,
        False,
        render_face_type_by_material_slot,
    )
    collision_data = mesh_to_vertices_faces(collision_object, depsgraph, True, None)
    if render_data is None or collision_data is None:
        return [True, "Failed to evaluate mesh data for export"]

    render_vertices, render_faces = render_data
    collision_vertices, collision_faces = collision_data
    collision_edges = build_edges(collision_faces)

    windows = []
    if windows_object is not None and windows_object.type == "MESH":
        windows = mesh_to_windows(windows_object, depsgraph)

    attachment_prefixes = (
        base_name + ".attachment.",
        base_name + ".wheel.",
    )
    attachments = []
    for obj in scene.objects:
        if obj.type != "EMPTY":
            continue

        matched_prefix = None
        for prefix in attachment_prefixes:
            if obj.name.startswith(prefix):
                matched_prefix = prefix
                break
        if matched_prefix is None:
            continue

        index_text = obj.name[len(matched_prefix) :]
        try:
            sort_index = int(index_text)
        except ValueError:
            sort_index = 0

        attachment_type = int(obj.get("sbv_attachment_type", 0))
        attachment_aux = float(obj.get("sbv_attachment_aux", 0.0))
        attachments.append(
            (sort_index, attachment_type, obj.location[:], attachment_aux)
        )

    attachments.sort(key=lambda attachment: attachment[0])

    with open(filepath, "wb") as f:
        f.write(pack("<i", 3))

        f.write(pack("<i", len(collision_vertices)))
        for vertex in collision_vertices:
            x, z, y = vertex
            f.write(pack("<fff", x, y, z))
            f.write(pack("<i", 0))

        f.write(pack("<i", len(collision_edges)))
        for edge in collision_edges:
            f.write(pack("<iii", 0, edge[0], edge[1]))

        f.write(pack("<i", len(collision_faces)))
        for face, _ in collision_faces:
            f.write(pack("<i", len(face)))
            for vertex_index in face:
                f.write(pack("<i", vertex_index))

        f.write(pack("<i", len(render_vertices)))
        for vertex in render_vertices:
            x, z, y = vertex
            f.write(pack("<fff", x, y, z))

        f.write(pack("<i", len(render_faces)))
        for face, face_type in render_faces:
            f.write(pack("<i", face_type))
            f.write(pack("<i", len(face)))

            for vertex_index in face:
                f.write(pack("<i", vertex_index))
                f.write(pack("<iiii", 0, 0, 0, 0))

            f.write(pack("<iiii", 0, 0, 0, 0))

        f.write(pack("<i", len(windows)))
        for window in windows:
            f.write(pack("<i", len(window)))

            for vertex in window:
                x, z, y = vertex
                f.write(pack("<fff", x, y, z))

        f.write(pack("<i", len(attachments)))
        for _, attachment_type, attachment_position, attachment_aux in attachments:
            f.write(pack("<i", attachment_type))
            x, z, y = attachment_position
            f.write(pack("<fff", x, y, z))
            f.write(pack("<f", attachment_aux))

    return [False, None]
