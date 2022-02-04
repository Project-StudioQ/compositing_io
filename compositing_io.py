import bpy
import json
from bpy_extras.io_utils import ImportHelper
from bpy.props import BoolProperty, IntProperty, PointerProperty, StringProperty
from . import compositing_load
from . import compositing_save

# ----------------------------------------------------------------------------------------------------
# 定数
# ----------------------------------------------------------------------------------------------------

TOOL_NAME = "Compositing Loader"

# ----------------------------------------------------------------------------------------------------
# PropertyGroup
# ----------------------------------------------------------------------------------------------------

class QCOMMON_SAVE_compositing_io(bpy.types.PropertyGroup):
    """ CompositorLoaderのプロパティ
    """
    load_path: StringProperty()
    is_clear_node: BoolProperty(default=True)
    is_clear_view_layer: BoolProperty(default=True)
    is_clear_freestyle: BoolProperty(default=True)
    is_clear_node_groups: BoolProperty(default=True)
    add_view_layer_name: StringProperty()
    import_count: IntProperty(default=0)

# ----------------------------------------------------------------------------------------------------
# Operator
# ----------------------------------------------------------------------------------------------------

class QCOMMON_OT_compositing_io_select_load_path(bpy.types.Operator, ImportHelper):
    """ 読込パスを選択
    """
    bl_idname = "qcommon.compositing_io_select_load_path"
    bl_label = "Select"

    filter_glob: StringProperty(
        default="*.blend",
        options={'HIDDEN'},
    )

    def execute(self, context):
        props = context.scene.compositing_io
        props.load_path = self.filepath
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
                    
        return {'FINISHED'}

class QCOMMON_OT_compositing_io_load(bpy.types.Operator):
    """ Compositingの設定を読込
    """
    bl_idname = "qcommon.compositing_io_load"
    bl_label = "Load"
    bl_description = "Load the Compositing settings as blender text"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.compositing_io
        if not props.load_path:
            return False
        else:
            return True

    def execute(self, context):
        props = context.scene.compositing_io

        json_data = compositing_load.load_compositing_option(props.load_path)
        if json_data == None:
            self.report({'ERROR'}, (
                f'{props.load_path}\n' + 
                'データの読み込みに失敗しました.\n' + 
                'compositingOptionが保存されていない可能性があります.'
            ))
            return {'CANCELLED'}

        # ViewLayerの設定
        if props.is_clear_view_layer:
            compositing_load.remove_view_layer(json_data)
            
        compositing_load.create_view_layer(json_data)
        is_success = compositing_load.set_render_layer(json_data, props.load_path)
        if not is_success:
            self.report({'ERROR'}, "ViewLayerの設定に失敗しました.")
            return {'CANCELLED'}

        # NodeGroupsの設定
        if props.is_clear_node_groups:
            compositing_load.remove_node_groups()
        compositing_load.append_node_groups(json_data)
        
        # Compositingの読み込み
        compositing_load.import_compositing(json_data, props.is_clear_node)

        return {'FINISHED'}

class QCOMMON_OT_compositing_io_export(bpy.types.Operator):
    """ Compositing設定をTempに書き出し
        ※元ファイルからバッチモードでアドオン呼び出し
    """
    bl_idname = "qcommon.compositing_io_export"
    bl_label = ""
    
    def execute(self, context):
        data = compositing_save.get_compositing_option()
        if data == None:
            self.report({'ERROR'}, f"Compositing Data None : {compositing_load.COMPOSITING_OPTION_NAME_TEMP_FILE}")
            return {'CANCELLED'}

        try:
            with open(compositing_load.COMPOSITING_OPTION_NAME_TEMP_FILE, "w") as f:
                json.dump(data, f)
        except:
            self.report({'ERROR'}, f"Export Failed : {compositing_load.COMPOSITING_OPTION_NAME_TEMP_FILE}")
            return {'CANCELLED'}
            
        self.report({'INFO'}, f"Export Success : {compositing_load.COMPOSITING_OPTION_NAME_TEMP_FILE}")
        return {'FINISHED'}
        
# ----------------------------------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------------------------------

class QCOMMON_PT_compositing_io_base(bpy.types.Panel):
    bl_label = "Compositing Loader"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.compositing_io

        col = layout.box().column()
        row = col.row(align=True)
        row.prop(props, "load_path", text="Load Path")
        row.operator(QCOMMON_OT_compositing_io_select_load_path.bl_idname, text="", icon="FILE_FOLDER")

        col.prop(props, "is_clear_node", text="Delete current CompositingNodes?")
        col.prop(props, "is_clear_view_layer", text="Delete current ViewLayers?")
        col.prop(props, "is_clear_freestyle", text="Delete current LineSet, LineStyle?")
        col.prop(props, "is_clear_node_groups", text="Delete current NodeGroups?")
        col.prop(props, "add_view_layer_name", text="Add ViewLayer Text")

        col = layout.column()
        col.operator(QCOMMON_OT_compositing_io_load.bl_idname, icon="IMPORT")

class QCOMMON_PT_compositing_io_mdl(QCOMMON_PT_compositing_io_base):
    bl_idname = "QCOMMON_PT_compositing_io_mdl"
    bl_category = "Q_COMMON"

# ----------------------------------------------------------------------------------------------------
# Register / Unregister
# ----------------------------------------------------------------------------------------------------

classes = (
    QCOMMON_SAVE_compositing_io,
    QCOMMON_OT_compositing_io_select_load_path,
    QCOMMON_OT_compositing_io_load,
    QCOMMON_OT_compositing_io_export,
    QCOMMON_PT_compositing_io_mdl,
)

def register():
    """ クラス登録
    """
    for i in classes:
        bpy.utils.register_class(i)
    
    bpy.types.Scene.compositing_io = PointerProperty(type=QCOMMON_SAVE_compositing_io)

def unregister():
    """ クラス登録解除
    """
    del(bpy.types.Scene.compositing_io)
    
    for i in classes:
        bpy.utils.unregister_class(i)