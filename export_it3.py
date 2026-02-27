import bpy
import bmesh
from struct import pack


def save(context: bpy.types.Context, filepath: str):
    with open(filepath, "wb") as f:
        f.write(pack("<i", 3))

        depsgraph = context.evaluated_depsgraph_get()
        scene = context.scene

        if bpy.context.active_object is not None:
            bpy.ops.object.mode_set(mode="OBJECT")

        it3_verts = []
        it3_faces = []

        for ob in scene.objects:
            if ob.type != "MESH":
                continue

            ob_for_convert = ob.evaluated_get(depsgraph)

            try:
                me = ob_for_convert.to_mesh()
            except RuntimeError:
                me = None

            if me is None:
                continue

            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.triangulate(bm, faces=bm.faces)

            uv_layer = bm.loops.layers.uv.verify()
            vertex_offset = len(it3_verts)

            for vertex in bm.verts:
                it3_verts.append(vertex.co[:])

            for face in bm.faces:
                it3_faces.append(
                    (
                        (
                            vertex_offset + face.verts[0].index,
                            vertex_offset + face.verts[1].index,
                            vertex_offset + face.verts[2].index,
                        ),
                        (
                            face.loops[0][uv_layer].uv[:],
                            face.loops[1][uv_layer].uv[:],
                            face.loops[2][uv_layer].uv[:],
                        ),
                    )
                )

            bm.free()
            ob_for_convert.to_mesh_clear()

        if len(it3_verts) == 0 or len(it3_faces) == 0:
            return {"CANCELLED"}

        f.write(pack("<ii", 0, 2))
        f.write(pack("<i", len(it3_verts)))
        for vertex in it3_verts:
            x, z, y = vertex
            f.write(pack("<fff", x, y, z))

        f.write(pack("<i", len(it3_faces)))
        for indices, uvs in it3_faces:
            f.write(pack("<i", 3))
            for i in range(3):
                f.write(pack("<i", indices[i]))
                u, v = uvs[i]
                f.write(pack("<ff", u, v))

        f.write(pack("<ii", 1, 1))
        f.write(pack("<i", 0))
        f.write(pack("<i", 0))

    return {"FINISHED"}
