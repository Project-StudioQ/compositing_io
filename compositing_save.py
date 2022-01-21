import bpy
from . import compositing_io_util as comp_util

# ----------------------------------------------------------------------------------------------------
# 定数
# ----------------------------------------------------------------------------------------------------

COMPOSITING_OPTION_NAME = "CompositingOption"

# ----------------------------------------------------------------------------------------------------
# Public Functions
# ----------------------------------------------------------------------------------------------------

# -- Get --

def get_compositing_option():
    """ Compositingの設定を取得

    Returns:
        Dictionary: Compositing設定
    """
    # 新規シーンなどはノードがない
    if bpy.context.scene.node_tree == None:
        return None

    # 標準情報の設定
    data = {}
    data["name"] = COMPOSITING_OPTION_NAME

    # 各プロパティの設定
    data["render_engine"] = bpy.context.scene.render.engine
    data["node_groups"] = _get_node_groups_names()
    data["nodes"] = _get_nodes_property(bpy.context.scene.node_tree)
    data["links"] = _get_links(bpy.context.scene.node_tree)
    data["render_layers"] = _search_in_render_layer_all()

    return data

# ----------------------------------------------------------------------------------------------------
# Private Functions
# ----------------------------------------------------------------------------------------------------

# -- Get --

def _get_node_groups_names():
    """ NodeGroupsの名称リストを取得

    Returns:
        str[]: NodeGroupsの名称リスト
    """
    node_groups_names = []
    
    for ng in bpy.data.node_groups:
        if ng.type != "COMPOSITING":
            continue
        if ng.library != None:
            continue
        
        node_groups_names.append(ng.name)
    
    return node_groups_names

def _get_nodes_property(tree):
    """ ノードリストのプロパティを取得

    Args:
        tree (bpy.types.NodeTree): ノードツリー

    Returns:
        Dictionary: ノードリストのプロパティ
    """
    nodes = {}
    for node in tree.nodes:
        prop = {}
        prop["auto_prop"] = _get_auto_property(node)

        sp_prop = {}
        # Parentの接続
        if node.parent != None:
            sp_prop["parent"] = node.parent.name
        # Groupの場合
        if node.bl_idname == "CompositorNodeGroup":
            sp_prop["group_name"] = node.node_tree.name
        # FileOutputの場合
        if node.bl_idname == "CompositorNodeOutputFile":
            sp_prop["format"] = _get_auto_property(node.format)
            sp_prop["layer_slots"] =  [slot.name for slot in node.layer_slots]
            sp_prop["file_slots"] =  [slot.path for slot in node.file_slots]

        _get_inputs(node, sp_prop)

        prop["sp_prop"] = sp_prop
        nodes[node.name] = prop

    return nodes

def _get_inputs(node, sp_prop):
    """ inputsの取得

    Args:
        node (bpy.types.Node): 対象ノード
        sp_prop (dict): 設定プロパティ
    """
    if not hasattr(node, "inputs"):
        return
    
    for i in node.inputs:
        try:
            if (i.bl_idname == "NodeSocketFloat" or 
                i.bl_idname == "NodeSocketFloatFactor"):
                sp_prop[i.identifier] = i.default_value
            elif i.bl_idname == "NodeSocketColor":
                sp_prop[i.identifier] = (i.default_value[0], i.default_value[1], i.default_value[2], i.default_value[3])
        except Exception as e:
            # FileOutputなどカラーで文字列が入ったりノードに応じて特殊パターンがあるため除外
            # 特殊パターンは別途ノードを判定して個別対応
            print(f"[{node.name}] {i.name} <- {i.identifier}  : {e}")

def _get_links(tree):
    """ リンク情報を取得

    Args:
        tree (bpy.types.NodeTree): ノードツリー

    Returns:
        Dictionary: リンク情報
    """
    links = {}
    count = 1
    for link in tree.links:
        link_data = {}
        link_data["from_node"] = link.from_node.name
        link_data["from_socket"] = link.from_socket.identifier
        link_data["to_node"] = link.to_node.name
        # FileOutputの場合にソケット名が生成時にはlayer_slots名になっている
        if link.to_node.bl_idname == "CompositorNodeOutputFile":
            index = None
            for i, input in enumerate(link.to_node.inputs):
                if input.identifier == link.to_socket.identifier:
                    index = i
                    break
            name = None
            # OpenEXR MultiLayerだとピンの名前の保存先が異なる
            if link.to_node.format.file_format == "OPEN_EXR_MULTILAYER":
                name = link.to_node.layer_slots[index].name
            else:
                name = link.to_node.file_slots[index].path
            link_data["to_socket"] = name
        else:
            link_data["to_socket"] = link.to_socket.identifier
        links[str(count).zfill(3)] = link_data
        count += 1

    return links

def _get_linestyle_names():
    """ 全てのLineStyleの名前を取得
    　　LineStyleは元データからAppend出来るので名前だけ取得

    Returns:
        Dictionary: 全てのLineStyleの名前
    """
    linestyle_names = []
    for ls in bpy.data.linestyles:
        linestyle_names.append(ls.name)
        
    return linestyle_names

def _search_in_render_layer_all():
    """ 全てのViewLayerのレンダリングプロパティを取得

    Returns:
        [type]: [description]
    """
    render_layer_settings = {}

    render_layer_settings["scene_use_freestyle"] = bpy.context.scene.render.use_freestyle
    render_layer_settings["linestyle_names"] = _get_linestyle_names()

    render_layer_props = {}
    for vl in bpy.context.scene.view_layers:
        render_layer_props[vl.name] = _search_in_render_layer( vl )
    render_layer_settings["render_layer_props"] = render_layer_props

    return render_layer_settings

def _search_in_render_layer(vl):
    """ ViewLayerのレンダリングプロパティを取得

    Args:
        vl (bpy.type.ViewLayer): ViewLayer

    Returns:
        Dictionary: ViewLayerのレンダリングプロパティ
    """
    render_layer = {}

    # Passes, Filters設定
    render_layer["vl_simple"] = _get_auto_property(vl)

    # AOV設定
    aovs = []
    target_aovs = None
    if hasattr( vl, "aovs" ):
        # 2.93以降
        target_aovs = vl.aovs
    else:
        # 2.91以前
        target_aovs = vl.cycles.aovs
    for aov in target_aovs:
        # 既にあったら追加しない
        target_aov = [a for a in aovs if a["name"] == aov.name]
        if len(target_aov):
            continue

        prop = {
            "name": aov.name
        ,   "type": aov.type
        }
        aovs.append(prop)
    render_layer["aovs"] = aovs

    # Freestyle設定
    if vl.freestyle_settings.as_render_pass:
        fs = {}
        fs["fs_simple"] = _get_auto_property(vl.freestyle_settings)

        linesets = {}
        for ls in vl.freestyle_settings.linesets:
            lineset = {}
            lineset["auto_props"] = _get_auto_property(ls)
            lineset["manual_props"] = _get_lineset_manual_props(ls)
            linesets[ls.name] = lineset
        fs["linesets"] = linesets

        render_layer["free_style"] = fs

    return render_layer

def _get_lineset_manual_props(lineset):
    """ LineSetの手動設定が必要なプロパティの取得

    Args:
        lineset (bpy.types.LineSet): 対象ラインセット

    Returns:
        Dictionary: LineSetの手動設定が必要なプロパティ
    """
    props = {}
    props["linestyle_name"] = lineset.linestyle.name
    
    return props

def _get_auto_property(obj):
    """ 自動取得出来るプロパティを取得

    Args:
        obj (Object): プロパティを取得するクラス

    Returns:
        Dictionary: 自動取得したプロパティ
    """
    auto_prop = {}

    for attr in dir(obj):
        if not hasattr(obj, attr):
            continue
        if _is_read_only_property(obj, attr):
            continue

        val = getattr(obj, attr)
        # そのまま代入できるものはそのまま
        if comp_util.can_substitute_type(val):
            auto_prop[attr] = val
        # Vectorはそのままdumps出来ないので変換
        if str(type(val)) == "<class 'Vector'>":
            auto_prop[attr] = (val[0], val[1])
        # Color
        if str(type(val)) == "<class 'Color'>":
            auto_prop[attr] = (val[0], val[1], val[2])
            
    return auto_prop

# -- Check --

def _is_read_only_property(obj, attr):
    """ 読み取り専用のプロパティか？

    Args:
        obj (Object): 対象オブジェクト
        attr (str): プロパティ名

    Returns:
        bool: True = Yes, Fale = No
    """
    is_read_only = False
    val = getattr(obj, attr)
    try:
        setattr(obj, attr, val)
    except:
        is_read_only = True
    return is_read_only