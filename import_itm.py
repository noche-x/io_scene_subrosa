import bpy
import json
from struct import unpack
from . import shared


ITM_HEADER_PROP = "itm_header"
ITM_PIVOT_A_PROP = "itm_pivot_a"
ITM_PIVOT_B_PROP = "itm_pivot_b"
ITM_MARKERS_PROP = "itm_markers_json"
ITM_MARKER_ID_PROP = "itm_marker_id"
ITM_MARKER_INDEX_PROP = "itm_marker_index"
ITM_MARKER_NAME_PROP = "itm_marker_name"

ITM_MARKER_NAME_BY_ID = {
    0: "muzzle_or_primary_anchor",
    1: "right_hand",
    2: "left_hand",
    4: "secondary_anchor",
}


def marker_name(marker_id: int) -> str:
    return ITM_MARKER_NAME_BY_ID.get(int(marker_id), "unknown_" + str(int(marker_id)))


def read_exact(f, size):
    data = f.read(size)
    assert len(data) == size, "Unexpected end of file."
    return data


def read_int(f):
    return unpack("<i", read_exact(f, 4))[0]


def read_uint(f):
    return unpack("<I", read_exact(f, 4))[0]


def read_vec3(f):
    return unpack("<fff", read_exact(f, 4 * 3))


def load(context, filepath):
    with open(filepath, "rb") as f:
        header = read_uint(f)
        pivot_a = read_vec3(f)
        pivot_b = read_vec3(f)

        markers = []
        marker_count = read_int(f)
        assert marker_count >= 0, "Invalid marker count."
        for _ in range(marker_count):
            marker_id = read_int(f)
            markers.append((marker_id, read_vec3(f)))

        vertices = []
        vertex_uvs = []

        vertex_count = read_int(f)
        assert vertex_count >= 0, "Invalid vertex count."
        for _ in range(vertex_count):
            x, y, z, u, v = unpack("<fffff", read_exact(f, 4 * 5))
            vertices.append((x - pivot_a[0], y - pivot_a[1], z - pivot_a[2]))
            vertex_uvs.append((u, v))

        faces = []

        face_count = read_int(f)
        assert face_count >= 0, "Invalid face count."
        for _ in range(face_count):
            num_vertices = read_int(f)
            assert num_vertices >= 3, "Invalid face vertex count."

            vertex_indices = []
            for _ in range(num_vertices):
                vertex_indices.append(read_int(f))

            if num_vertices <= 4:
                faces.append(tuple(vertex_indices))
            else:
                for i in range(1, num_vertices - 1):
                    faces.append(
                        (vertex_indices[0], vertex_indices[i], vertex_indices[i + 1])
                    )

        name = bpy.path.display_name_from_filepath(filepath)
        shared.load_mesh(context, name, vertices, faces, vertex_uvs, None, None)

        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj[ITM_HEADER_PROP] = int(header)
            obj[ITM_PIVOT_A_PROP] = [
                float(pivot_a[0]),
                float(pivot_a[1]),
                float(pivot_a[2]),
            ]
            obj[ITM_PIVOT_B_PROP] = [
                float(pivot_b[0]),
                float(pivot_b[1]),
                float(pivot_b[2]),
            ]

            marker_data = []
            collection = context.view_layer.active_layer_collection.collection
            for i, marker in enumerate(markers):
                marker_id, position = marker
                local_position = (
                    position[0] - pivot_a[0],
                    position[2] - pivot_a[2],
                    position[1] - pivot_a[1],
                )
                marker_data.append(
                    {
                        "id": int(marker_id),
                        "pos": [
                            local_position[0],
                            local_position[1],
                            local_position[2],
                        ],
                    }
                )

                friendly_name = marker_name(marker_id)
                empty = bpy.data.objects.new(
                    name
                    + ".marker."
                    + str(i)
                    + "."
                    + str(marker_id)
                    + "."
                    + friendly_name,
                    None,
                )
                empty.empty_display_type = "ARROWS"
                empty.empty_display_size = 0.05
                empty.location = local_position
                empty.parent = obj
                empty[ITM_MARKER_ID_PROP] = int(marker_id)
                empty[ITM_MARKER_INDEX_PROP] = int(i)
                empty[ITM_MARKER_NAME_PROP] = friendly_name
                collection.objects.link(empty)

            obj[ITM_MARKERS_PROP] = json.dumps(marker_data)

    return {"FINISHED"}
