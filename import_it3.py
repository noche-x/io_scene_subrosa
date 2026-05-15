import bpy
import mathutils
from struct import unpack
from . import shared


def load(context, filepath):
    with open(filepath, "rb") as f:

        def read(size):
            data = f.read(size)
            assert len(data) == size, "Unexpected end of file."
            return data

        (version,) = unpack("<i", read(4))
        assert version == 3, "Unknown file version."

        vertices = []
        faces = []
        loop_uvs = []

        (section_id,) = unpack("<i", read(4))
        assert section_id == 0, "Expected section 0."

        (sub_type,) = unpack("<i", read(4))
        assert sub_type == 2, "Expected sub_type 2."

        (vertex_count,) = unpack("<i", read(4))
        assert vertex_count >= 0, "Invalid vertex count."
        for _ in range(vertex_count):
            vertices.append(unpack("<fff", read(4 * 3)))

        (face_count,) = unpack("<i", read(4))
        assert face_count >= 0, "Invalid face count."
        for _ in range(face_count):
            (num_vertices,) = unpack("<i", read(4))
            assert num_vertices >= 0, "Invalid face vertex count."

            vertex_indices = []
            vertex_uvs = []
            for _ in range(num_vertices):
                (vertex_id,) = unpack("<i", read(4))
                assert vertex_id >= 0, "Invalid vertex index."
                vertex_indices.append(vertex_id)
                vertex_uvs.append(unpack("<ff", read(4 * 2)))

            if num_vertices == 3:
                faces.append((vertex_indices[0], vertex_indices[1], vertex_indices[2]))
                loop_uvs.extend((vertex_uvs[0], vertex_uvs[1], vertex_uvs[2]))
            elif num_vertices == 4:
                faces.append((vertex_indices[0], vertex_indices[1], vertex_indices[2]))
                loop_uvs.extend((vertex_uvs[0], vertex_uvs[1], vertex_uvs[2]))

                faces.append((vertex_indices[0], vertex_indices[2], vertex_indices[3]))
                loop_uvs.extend((vertex_uvs[0], vertex_uvs[2], vertex_uvs[3]))
            else:
                assert False, "Unknown face vertex count."

        (section_id,) = unpack("<i", read(4))
        assert section_id == 1, "Expected section 1."

        (sub_type,) = unpack("<i", read(4))
        assert sub_type == 1, "Expected sub_type 1."

        (group_vertex_count,) = unpack("<i", read(4))
        assert group_vertex_count >= 0, "Invalid group vertex count."
        read(4 * 3 * group_vertex_count)

        (group_count,) = unpack("<i", read(4))
        assert group_count >= 0, "Invalid group count."
        for _ in range(group_count):
            read(4 * 3)

            (vertex_count,) = unpack("<i", read(4))
            assert vertex_count >= 0, "Invalid group index count."
            read(4 * vertex_count)

            (group_face_count,) = unpack("<i", read(4))
            assert group_face_count >= 0, "Invalid group face count."
            for _ in range(group_face_count):
                (num_vertices,) = unpack("<i", read(4))
                assert num_vertices >= 0, "Invalid group face vertex count."
                read(4 * num_vertices)

        name = bpy.path.display_name_from_filepath(filepath)
        shared.load_mesh(context, name, vertices, faces, None, None, None)

        obj = context.view_layer.objects.active
        assert obj is not None and obj.type == "MESH", "Failed to create object."
        mesh = obj.data
        assert len(loop_uvs) == len(mesh.loops), "Invalid UV count."

        layer = mesh.uv_layers.new(do_init=True)
        for i, loop in enumerate(mesh.loops):
            layer.uv[loop.index].vector = mathutils.Vector(loop_uvs[i])

    return {"FINISHED"}
