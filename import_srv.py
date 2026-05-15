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


def read_mesh_block(f):
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

    return vertices, faces, loop_uvs


def load_v1(context, f, name):
    bounds_count = read_int(f)
    for _ in range(bounds_count):
        read_exact(f, 4 * 6)

    read_int(f)
    vertices, faces, loop_uvs = read_mesh_block(f)
    shared.load_mesh(
        context, name + ".collision", vertices, faces, None, None, None, loop_uvs
    )

    child_mesh_count = read_int(f)
    for i in range(child_mesh_count):
        vertices, faces, loop_uvs = read_mesh_block(f)
        child_name = name
        if i != 0:
            child_name = name + ".child." + str(i)

        shared.load_mesh(
            context,
            child_name,
            vertices,
            faces,
            None,
            None,
            None,
            loop_uvs,
        )

    trailing = f.read()
    assert len(trailing) == 0, "Unexpected trailing bytes."


def load(context, filepath, expected_version=None):
    with open(filepath, "rb") as f:
        version = read_int(f)
        if expected_version is not None:
            assert version == expected_version, "Unexpected .srv file version."

        name = bpy.path.display_name_from_filepath(filepath)
        if version == 1:
            load_v1(context, f, name)
        else:
            assert False, "Unknown .srv file version."

    return {"FINISHED"}
