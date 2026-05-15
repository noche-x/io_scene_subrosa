import bpy
from struct import unpack
from . import shared


def load(context, filepath):
    with open(filepath, "rb") as f:
        (version,) = unpack("<i", f.read(4))
        assert version <= 5, "Unknown file version."

        collision_vertices = []
        collision_faces = []

        if version >= 5:
            f.read(4 * 3)

        (collision_vertex_count,) = unpack("<i", f.read(4))
        for _ in range(collision_vertex_count):
            collision_vertices.append(unpack("<fff", f.read(4 * 3)))
            f.read(4)

        (edge_count,) = unpack("<i", f.read(4))
        f.read(4 * 3 * edge_count)

        (collision_face_count,) = unpack("<i", f.read(4))
        for _ in range(collision_face_count):
            (num_vertices,) = unpack("<i", f.read(4))
            vertex_indices = []

            for _ in range(num_vertices):
                (vertex_id,) = unpack("<i", f.read(4))
                vertex_indices.append(vertex_id)

            vertex_indices.reverse()
            collision_faces.append(tuple(vertex_indices))

        vertices = []
        faces = []
        loop_uvs = []

        (vertex_count,) = unpack("<i", f.read(4))
        for _ in range(vertex_count):
            vertices.append(unpack("<fff", f.read(4 * 3)))

        (face_count,) = unpack("<i", f.read(4))
        for _ in range(face_count):
            face_type = 0
            if version >= 3:
                (face_type,) = unpack("<i", f.read(4))

            (num_vertices,) = unpack("<i", f.read(4))
            vertex_indices = []

            for _ in range(num_vertices):
                (vertex_id,) = unpack("<i", f.read(4))
                vertex_indices.append(vertex_id)

                if version >= 2:
                    f.read(4 * 4)

            if version >= 2:
                f.read(4 * 4)

            faces.append(tuple(vertex_indices))

            if face_type == 1:
                uv = (0.0, 1.0)
            elif face_type == 2:
                uv = (0.09375, 0.09375)
            else:
                uv = (16.5, 0.0)
            for _ in range(num_vertices):
                loop_uvs.append(uv)

        window_vertices = []
        window_faces = []

        (window_count,) = unpack("<i", f.read(4))
        for _ in range(window_count):
            (num_vertices,) = unpack("<i", f.read(4))
            vertex_indices = []

            for _ in range(num_vertices):
                vertex_indices.append(len(window_vertices))
                window_vertices.append(unpack("<fff", f.read(4 * 3)))

            vertex_indices.reverse()
            window_faces.append(tuple(vertex_indices))

        attachments = []
        (attachment_count,) = unpack("<i", f.read(4))
        for _ in range(attachment_count):
            (attachment_type,) = unpack("<i", f.read(4))
            attachment_position = unpack("<fff", f.read(4 * 3))
            (attachment_aux,) = unpack("<f", f.read(4))
            attachments.append((attachment_type, attachment_position, attachment_aux))

        name = bpy.path.display_name_from_filepath(filepath)
        shared.load_mesh(context, name, vertices, faces, None, None, None, loop_uvs)
        shared.load_mesh(
            context,
            name + ".collision",
            collision_vertices,
            collision_faces,
            None,
            None,
            None,
        )
        shared.load_mesh(
            context, name + ".windows", window_vertices, window_faces, None, None, None
        )

        collection = context.view_layer.active_layer_collection.collection
        for i, attachment in enumerate(attachments):
            attachment_type, attachment_position, attachment_aux = attachment

            attachment_name = name + ".wheel." + str(i)
            attachment_obj = bpy.data.objects.new(attachment_name, None)
            attachment_obj.empty_display_type = "PLAIN_AXES"
            attachment_obj.location = (
                attachment_position[0],
                attachment_position[2],
                attachment_position[1],
            )
            attachment_obj["sbv_attachment_role"] = "wheel"
            attachment_obj["sbv_attachment_type"] = attachment_type
            attachment_obj["sbv_attachment_aux"] = attachment_aux
            collection.objects.link(attachment_obj)

    return {"FINISHED"}
