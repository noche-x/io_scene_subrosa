import bpy
from struct import unpack
from . import shared


def read_exact(f, size):
    data = f.read(size)
    assert len(data) == size, "Unexpected end of file."
    return data


def read_int(f):
    return unpack("<i", read_exact(f, 4))[0]


def read_vec3(f):
    return unpack("<fff", read_exact(f, 4 * 3))


def read_face(f):
    num_vertices = read_int(f)
    assert num_vertices in (3, 4), "Unknown face vertex count."

    vertex_indices = []
    loop_uvs = []
    for _ in range(num_vertices):
        vertex_indices.append(read_int(f))
        loop_uvs.append(unpack("<ff", read_exact(f, 4 * 2)))

    return tuple(vertex_indices), loop_uvs


def load_window_curve(context, name, points):
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"

    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for i, point in enumerate(points):
        spline.points[i].co = (point[0], point[2], point[1], 1.0)
    spline.use_cyclic_u = True

    obj = bpy.data.objects.new(name, curve)
    collection = context.view_layer.active_layer_collection.collection
    collection.objects.link(obj)
    obj.select_set(True)


def load_v1(context, f, name):
    vertices = []
    faces = []
    loop_uvs = []

    point_count = read_int(f)
    for _ in range(point_count):
        vertices.append(read_vec3(f))

    face_count = read_int(f)
    for _ in range(face_count):
        face, face_uvs = read_face(f)
        faces.append(face)
        loop_uvs.extend(face_uvs)

    attachment_version = read_int(f)
    assert attachment_version == 1, "Unknown .tst v1 attachment version."

    window_count = read_int(f)
    windows = []
    for _ in range(window_count):
        window_point_count = read_int(f)
        windows.append([read_vec3(f) for _ in range(window_point_count)])

    shared.load_mesh(context, name, vertices, faces, None, None, None, loop_uvs)
    for i, window in enumerate(windows):
        load_window_curve(context, name + ".window." + str(i), window)


def load_v2(context, f, name):
    vertices = []
    faces = []
    loop_uvs = []

    read_int(f)

    point_count = read_int(f)
    for _ in range(point_count):
        vertices.append(read_vec3(f))
        read_int(f)

    face_count = read_int(f)
    for _ in range(face_count):
        face, face_uvs = read_face(f)
        read_int(f)

        faces.append(face)
        loop_uvs.extend(face_uvs)

    shared.load_mesh(context, name, vertices, faces, None, None, None, loop_uvs)


def load(context, filepath, expected_version=None):
    with open(filepath, "rb") as f:
        version = read_int(f)
        if expected_version is not None:
            assert version == expected_version, "Unexpected .tst file version."

        name = bpy.path.display_name_from_filepath(filepath)
        if version == 1:
            load_v1(context, f, name)
        elif version == 2:
            load_v2(context, f, name)
        else:
            assert False, "Unknown .tst file version."

    return {"FINISHED"}
