import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper


class ImportCMO(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Object File"""

    bl_idname = "import_scene.cmo"
    bl_label = "Import CMO"
    bl_options = {"UNDO"}

    filename_ext = ".cmo"
    filter_glob = StringProperty(default="*.cmo", options={"HIDDEN"})

    def execute(self, context):
        from . import import_cmo

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_cmo.load(context, **keywords)


class ImportCMC(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Character File"""

    bl_idname = "import_scene.cmc"
    bl_label = "Import CMC"
    bl_options = {"UNDO"}

    filename_ext = ".cmo"
    filter_glob = StringProperty(default="*.cmc", options={"HIDDEN"})

    def execute(self, context):
        from . import import_cmc

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_cmc.load(context, **keywords)


class ImportITM(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Item File"""

    bl_idname = "import_scene.itm"
    bl_label = "Import ITM"
    bl_options = {"UNDO"}

    filename_ext = ".itm"
    filter_glob = StringProperty(default="*.itm", options={"HIDDEN"})

    def execute(self, context):
        from . import import_itm

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_itm.load(context, **keywords)


class ImportSIT(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Legacy Item File"""

    bl_idname = "import_scene.sit"
    bl_label = "Import SIT"
    bl_options = {"UNDO"}

    filename_ext = ".sit"
    filter_glob = StringProperty(default="*.sit", options={"HIDDEN"})

    def execute(self, context):
        from . import import_sit

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_sit.load(context, **keywords)


class ImportSBV(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Vehicle File"""

    bl_idname = "import_scene.sbv"
    bl_label = "Import SBV"
    bl_options = {"UNDO"}

    filename_ext = ".sbv"
    filter_glob = StringProperty(default="*.sbv", options={"HIDDEN"})

    def execute(self, context):
        from . import import_sbv

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_sbv.load(context, **keywords)


class ImportTSTV1(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa TST v1 Vehicle File"""

    bl_idname = "import_scene.tst_v1"
    bl_label = "Import TST v1"
    bl_options = {"UNDO"}

    filename_ext = ".tst"
    filter_glob = StringProperty(default="*.tst", options={"HIDDEN"})

    def execute(self, context):
        from . import import_tst

        keywords = self.as_keywords(ignore=("filter_glob",))
        keywords["expected_version"] = 1
        return import_tst.load(context, **keywords)


class ImportTSTV2(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa TST v2 Vehicle File"""

    bl_idname = "import_scene.tst_v2"
    bl_label = "Import TST v2"
    bl_options = {"UNDO"}

    filename_ext = ".tst"
    filter_glob = StringProperty(default="*.tst", options={"HIDDEN"})

    def execute(self, context):
        from . import import_tst

        keywords = self.as_keywords(ignore=("filter_glob",))
        keywords["expected_version"] = 2
        return import_tst.load(context, **keywords)


class ImportSRVV1(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa SRV v1 Vehicle File"""

    bl_idname = "import_scene.srv_v1"
    bl_label = "Import SRV v1"
    bl_options = {"UNDO"}

    filename_ext = ".srv"
    filter_glob = StringProperty(default="*.srv", options={"HIDDEN"})

    def execute(self, context):
        from . import import_srv

        keywords = self.as_keywords(ignore=("filter_glob",))
        keywords["expected_version"] = 1
        return import_srv.load(context, **keywords)


class ImportIT3(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Interactive Object File"""

    bl_idname = "import_scene.it3"
    bl_label = "Import IT3"
    bl_options = {"UNDO"}

    filename_ext = ".it3"
    filter_glob = StringProperty(default="*.it3", options={"HIDDEN"})

    def execute(self, context):
        from . import import_it3

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_it3.load(context, **keywords)


class SubRosaImportMenu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_subrosa_import"
    bl_label = "Sub Rosa"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportCMO.bl_idname, text="Object (.cmo)")
        layout.operator(ImportCMC.bl_idname, text="Character (.cmc)")
        layout.operator(ImportITM.bl_idname, text="Item (.itm)")
        layout.operator(ImportSIT.bl_idname, text="Legacy Item (.sit)")
        layout.operator(ImportIT3.bl_idname, text="Item / Interactive Object (.it3)")
        layout.separator()
        layout.operator(ImportSBV.bl_idname, text="Vehicle SBV (.sbv)")
        layout.operator(ImportTSTV1.bl_idname, text="Vehicle TST v1 (.tst)")
        layout.operator(ImportTSTV2.bl_idname, text="Vehicle TST v2 (.tst)")
        layout.operator(ImportSRVV1.bl_idname, text="Vehicle SRV v1 (.srv)")


def menu_func_import(self, context):
    self.layout.menu(SubRosaImportMenu.bl_idname, text="Sub Rosa")


class ExportCMO(bpy.types.Operator, ExportHelper):
    """Export a Sub Rosa Object File"""

    bl_idname = "export_scene.cmo"
    bl_label = "Export CMO"

    filename_ext = ".cmo"
    filter_glob = StringProperty(default="*.cmo", options={"HIDDEN"})

    def execute(self, context):
        from . import export_cmo

        keywords = self.as_keywords(ignore=("filter_glob", "check_existing"))
        return export_cmo.save(context, **keywords)


class ExportCMC(bpy.types.Operator, ExportHelper):
    """Export a Sub Rosa Character File"""

    bl_idname = "export_scene.cmc"
    bl_label = "Export CMC"

    filename_ext = ".cmc"
    filter_glob = StringProperty(default="*.cmc", options={"HIDDEN"})

    def execute(self, context):
        from . import export_cmc

        keywords = self.as_keywords(ignore=("filter_glob", "check_existing"))
        didError, message = export_cmc.save(context, **keywords)
        if didError:
            self.report({"INFO"}, message)
            return {"CANCELLED"}

        return {"FINISHED"}


class ExportSBV(bpy.types.Operator, ExportHelper):
    """Export a Sub Rosa Vehicle File"""

    bl_idname = "export_scene.sbv"
    bl_label = "Export SBV"

    filename_ext = ".sbv"
    filter_glob = StringProperty(default="*.sbv", options={"HIDDEN"})

    def execute(self, context):
        from . import export_sbv

        keywords = self.as_keywords(ignore=("filter_glob", "check_existing"))
        didError, message = export_sbv.save(context, **keywords)
        if didError:
            self.report({"INFO"}, message)
            return {"CANCELLED"}

        return {"FINISHED"}


class ExportTSTV1(bpy.types.Operator, ExportHelper):
    """Export a Sub Rosa TST v1 Vehicle File"""

    bl_idname = "export_scene.tst_v1"
    bl_label = "Export TST v1"

    filename_ext = ".tst"
    filter_glob = StringProperty(default="*.tst", options={"HIDDEN"})

    def execute(self, context):
        from . import export_tst

        keywords = self.as_keywords(ignore=("filter_glob", "check_existing"))
        didError, message = export_tst.save(context, version=1, **keywords)
        if didError:
            self.report({"INFO"}, message)
            return {"CANCELLED"}

        return {"FINISHED"}


class ExportTSTV2(bpy.types.Operator, ExportHelper):
    """Export a Sub Rosa TST v2 Vehicle File"""

    bl_idname = "export_scene.tst_v2"
    bl_label = "Export TST v2"

    filename_ext = ".tst"
    filter_glob = StringProperty(default="*.tst", options={"HIDDEN"})

    def execute(self, context):
        from . import export_tst

        keywords = self.as_keywords(ignore=("filter_glob", "check_existing"))
        didError, message = export_tst.save(context, version=2, **keywords)
        if didError:
            self.report({"INFO"}, message)
            return {"CANCELLED"}

        return {"FINISHED"}


class ExportSRVV1(bpy.types.Operator, ExportHelper):
    """Export a Sub Rosa SRV v1 Vehicle File"""

    bl_idname = "export_scene.srv_v1"
    bl_label = "Export SRV v1"

    filename_ext = ".srv"
    filter_glob = StringProperty(default="*.srv", options={"HIDDEN"})

    def execute(self, context):
        from . import export_srv

        keywords = self.as_keywords(ignore=("filter_glob", "check_existing"))
        didError, message = export_srv.save(context, version=1, **keywords)
        if didError:
            self.report({"INFO"}, message)
            return {"CANCELLED"}

        return {"FINISHED"}


class ExportIT3(bpy.types.Operator, ExportHelper):
    """Export a Sub Rosa Interactive Object File"""

    bl_idname = "export_scene.it3"
    bl_label = "Export IT3"

    filename_ext = ".it3"
    filter_glob = StringProperty(default="*.it3", options={"HIDDEN"})

    def execute(self, context):
        from . import export_it3

        keywords = self.as_keywords(ignore=("filter_glob", "check_existing"))
        return export_it3.save(context, **keywords)


class SubRosaExportMenu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_subrosa_export"
    bl_label = "Sub Rosa"

    def draw(self, context):
        layout = self.layout
        layout.operator(ExportCMO.bl_idname, text="Object (.cmo)")
        layout.operator(ExportCMC.bl_idname, text="Character (.cmc)")
        layout.operator(ExportIT3.bl_idname, text="Item / Interactive Object (.it3)")
        layout.separator()
        layout.operator(ExportSBV.bl_idname, text="Vehicle SBV (.sbv)")
        layout.operator(ExportTSTV1.bl_idname, text="Vehicle TST v1 (.tst)")
        layout.operator(ExportTSTV2.bl_idname, text="Vehicle TST v2 (.tst)")
        layout.operator(ExportSRVV1.bl_idname, text="Vehicle SRV v1 (.srv)")


def menu_func_export(self, context):
    self.layout.menu(SubRosaExportMenu.bl_idname, text="Sub Rosa")


classes = (
    SubRosaImportMenu,
    SubRosaExportMenu,
    ImportCMO,
    ImportCMC,
    ImportITM,
    ImportSIT,
    ImportSBV,
    ImportTSTV1,
    ImportTSTV2,
    ImportSRVV1,
    ImportIT3,
    ExportCMO,
    ExportCMC,
    ExportSBV,
    ExportTSTV1,
    ExportTSTV2,
    ExportSRVV1,
    ExportIT3,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)
