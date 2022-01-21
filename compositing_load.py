import bpy
import os
import subprocess
import json
import uuid
import tempfile
from . import compositing_io_util as comp_util

# ----------------------------------------------------------------------------------------------------
# 定数
# ----------------------------------------------------------------------------------------------------

COMPOSITING_OPTION_NAME_TEMP_FILE = os.path.join(tempfile.gettempdir(), "compositing_option.json")
DATA_NODE_GROUPS = "/NodeTree/"
NODE_MARGIN = 300
DEFAULT_VIEW_LAYER = "View Layer"
DATA_FREESTYLE_LINESTYLE = "/FreestyleLineStyle/"

DEFAULT_AOV_SORT_LIST = [
    "transparent"
,   "hl"
,   "normal"
,   "sdw1"
,   "sdw2"
,   "msk"
,   "fresnel"
,   "position"
,   "tanjentNormal"
]

# ----------------------------------------------------------------------------------------------------
# Public Functions
# ----------------------------------------------------------------------------------------------------

# -- Set --

def set_render_layer(json_data, load_path):
    """ RenderLayerの設定

    Args:
        json_data (Dictionary): RenderLayerの設定データ

    Returns:
        bool: True = 設定成功, False = 失敗
    """
    if not "render_layers" in json_data:
        return False

    render_layer_settings = json_data["render_layers"]

    if "render_layer_props" not in render_layer_settings:
        return False

    bpy.context.scene.render.use_freestyle = render_layer_settings["scene_use_freestyle"]    
    _set_linestyles(render_layer_settings, load_path)
    _set_view_layer_props(render_layer_settings)
                
    return True

def load_compositing_option(load_path):
    """ Compositing設定を読み込んでDictionaryで取得

    Args:
        load_path (str): 読み込みパス

    Returns:
        Dictionary: Compositing設定
    """
    # 前のファイルを読み込まないように念のため削除
    if os.path.isfile(COMPOSITING_OPTION_NAME_TEMP_FILE):
        os.remove(COMPOSITING_OPTION_NAME_TEMP_FILE)
    
    # 元ファイルから設定を%temp%に出力
    script_path = os.path.join(os.path.dirname(__file__), "export_compositing.py")
    result = subprocess.run([
        bpy.app.binary_path,
        "-b",
        load_path,
        "-P",
        script_path
    ])
    if result.returncode != 0:
        print("Crash Blender when save Compositing to temporary directory.")
        return None

    try:
        with open(COMPOSITING_OPTION_NAME_TEMP_FILE, 'r') as f:
            json_data = json.load(f)
    except Exception as e:
        print("Can't load Compositing from {load_path}")
        return None

    return json_data

def import_compositing(json_data, is_clear):
    """ Compositing設定を読み込み

    Args:
        is_clear (bool): 既存のデータをクリアするか？
    """
    bpy.context.scene.use_nodes = True

    tree = bpy.context.scene.node_tree
    old_nodes = [n for n in tree.nodes]
    nodes = _create_nodes(json_data, tree, is_clear)
    _create_links(json_data, tree, is_clear)

    props = bpy.context.scene.compositing_io
    if is_clear:
        props.import_count = 0

    # 名前が被ると接続先が前のノードになるので、
    # 生成時にユニークな名前に変える
    for node in nodes:
        guid = uuid.uuid4()
        node.name = f"{node.name}[{guid}]"
        node.update()
    props.import_count += 1

    # 連続生成する際は位置を調整
    # TODO Frameノードの位置の取得がバグっているのでFrameノードがあるとズレる
    # 以下でBlender側自体の対応が行われているが対応が止まっている
    # https://developer.blender.org/T72904
    if not is_clear and props.import_count > 0:
        bottomPos = _calc_nodes_bottom_position(old_nodes)
        topPos = _calc_nodes_top_position(nodes)
        diffPos = abs(topPos - bottomPos) + NODE_MARGIN
        for node in nodes:
            node.location[1] -= diffPos

    return nodes

def create_view_layer(json_data):
    """ View Layerを生成

    Args:
        json_data (Dictionary): Compositingオプション
    """
    render_layers = json_data["render_layers"]
    render_layer_props = render_layers["render_layer_props"]
    for rl_prop in render_layer_props:
        vl_name = _calc_view_layer_name(rl_prop)
        # 既に作成されていたら作らない
        if vl_name in bpy.context.scene.view_layers:
            continue
        bpy.context.scene.view_layers.new(vl_name)

def remove_view_layer(json_data):
    """ JsonDataに含まれないViewLayerを削除

    Args:
        json_data (Dictionary): Compositingオプション
    """
    render_layers = json_data["render_layers"]
    render_layer_props = render_layers["render_layer_props"]
    for vl in bpy.context.scene.view_layers:
        if vl.name in render_layer_props:
            continue
        bpy.context.scene.view_layers.remove(vl)

def remove_view_layers_ignore_default():
    """ デフォルトのViewLayer以外を削除
    """
    def_layer = bpy.context.scene.view_layers[DEFAULT_VIEW_LAYER]
    bpy.context.window.view_layer = def_layer
    for layer in bpy.context.scene.view_layers:
        if layer == def_layer:
            continue
        bpy.context.scene.view_layers.remove(layer)

def append_node_groups(json_data):
    """ NodeGroupsを一括アペンド

    Args:
        json_data (Dictionary): Compositingオプション
    """
    props = bpy.context.scene.compositing_io
    
    for ng in json_data["node_groups"]:
        directory = props.load_path + DATA_NODE_GROUPS
        bpy.ops.wm.append(directory=directory, filename=ng, use_recursive=False)

def remove_node_groups():
    """ ノードグループを一括削除
    """
    for ng in bpy.data.node_groups:
        if ng.type != "COMPOSITING":
            continue
        if ng.library != None:
            continue

        bpy.data.node_groups.remove(ng)
        
# -- Get --

def get_render_engine(option):
    """ RenderEngineを取得

    Args:
        option (Dictionary): Compositing設定

    Returns:
        str: RenderEngineのタイプ
    """
    return option["render_engine"]
        
# ----------------------------------------------------------------------------------------------------
# Private Functions
# ----------------------------------------------------------------------------------------------------
        
# -- Get --

def _calc_nodes_bottom_position(nodes):
    """ ノードリストの下端位置を取得

    Args:
        nodes (bpy.types.Nodes): ノードリスト

    Returns:
        float: 下端の位置
    """
    bottomPos = None
    # ノードがなかったら初期位置に
    if len(nodes) <= 0:
        return 0

    for node in nodes:
        # 高さの分下げる
        posY = node.location[1] - node.dimensions[1]
        if bottomPos == None or bottomPos > posY:
            bottomPos = posY

    return bottomPos

def _calc_nodes_top_position(nodes):
    """ ノードリストの上端位置を取得

    Args:
        nodes (bpy.types.Nodes): ノードリスト

    Returns:
        float: 上端の位置
    """
    topPos = None
    for node in nodes:
        posY = node.location[1]
        if topPos == None or topPos < posY:
            topPos = posY
    return topPos

def _calc_view_layer_name(view_layer_name):
    """ プロパティを元にViewLayer名を取得

    Args:
        view_layer_name (str): 元ViewLayer名

    Returns:
        str: ViewLayer名
    """
    props = bpy.context.scene.compositing_io
    if view_layer_name == DEFAULT_VIEW_LAYER or props.add_view_layer_name == "":
        return view_layer_name
    else:
        return props.add_view_layer_name + view_layer_name
        
# -- Set --
        
def _set_auto_property(auto_prop, obj):
    """ そのまま代入できるプロパティを設定

    Args:
        auto_prop (Dictionary): そのまま代入出来るプロパティのディクショナリー
        obj (Object): 代入するクラス
    """
    for attr in auto_prop.keys():
        if not hasattr(obj, attr):
            continue

        val = auto_prop[attr]
        if comp_util.can_substitute_type(val):
            try:
                setattr(obj, attr, val)
            except Exception as e:
                # 存在しないViewLayerの場合に弾かれるがリネームの影響なので除外
                print(e)
                pass
        elif len(val) == 2:
            setattr(obj, attr, (val[0], val[1]))
        elif len(val) == 3:
            setattr(obj, attr, (val[0], val[1], val[2]))
        
def _create_nodes(json_data, tree, is_clear):
    """ オプションからノードを生成

    Args:
        json_data (Dictionary): オプションデータ
        tree (bpy.types.NodeTree): ノードツリー
        is_clear (bool): 既存のノードをクリアするか？

    Returns:
        bpy.types.BlendDataNodeTrees: 生成したノード
    """
    nodes = []
    nodes_data = json_data["nodes"]
    if is_clear:
        tree.nodes.clear()
    for key in nodes_data.keys():
        node_prop = nodes_data[key]

        # 自動取得したプロパティの設定
        auto_prop = node_prop["auto_prop"]
        try:
            node = tree.nodes.new(type=auto_prop["bl_idname"])
        except:
            print(auto_prop)
            continue
        _set_auto_property(auto_prop, node)
          
        sp_prop = node_prop["sp_prop"]
        # Parentの設定
        if "parent" in sp_prop:
            node.parent = tree.nodes[sp_prop["parent"]]
        
        # Groupの場合
        if node.bl_idname == "CompositorNodeGroup":
            if sp_prop["group_name"] in bpy.data.node_groups:
                node.node_tree = bpy.data.node_groups[sp_prop["group_name"]]
        # FileOutputの場合
        elif node.bl_idname == "CompositorNodeOutputFile":
            _set_auto_property(sp_prop["format"], node.format)
            if node.format.file_format == "OPEN_EXR_MULTILAYER":
                node.layer_slots.clear()
                for name in sp_prop["layer_slots"]:
                    node.layer_slots.new(name)
            else:
                node.file_slots.clear()
                for name in sp_prop["file_slots"]:
                    node.file_slots.new(name)
        # RenderLayersの場合
        elif node.bl_idname == "CompositorNodeRLayers":
            node.layer = _calc_view_layer_name(auto_prop["layer"])

        _set_inputs(node, sp_prop)

        nodes.append(node)

    return nodes

def _set_inputs(node, sp_prop):
    """ inputの設定

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
                i.default_value = sp_prop[i.identifier]
            elif i.bl_idname == "NodeSocketColor":
                color_val = sp_prop[i.identifier]
                i.default_value = (color_val[0], color_val[1], color_val[2], color_val[3])
        except Exception as e:
            # FileOutputなどカラーで文字列が入ったりノードに応じて特殊パターンがあるため除外
            # 特殊パターンは別途ノードを判定して個別対応
            print(f"[{node.name}] {i.name} <- {i.identifier} : {e}")


def _create_links(json_data, tree, is_clear):
    """ リンク情報を生成

    Args:
        json_data (Dictionary): オプションデータ
        tree (bpy.types.NodeTree): ノードツリー
        is_clear (bool): 既存のリンクをクリアするか？

    Returns:
        bpy.types.NodeLinks: 生成したリンク
    """
    if is_clear:
        tree.links.clear()
    links = []
    links_data = json_data["links"]
    for key in links_data.keys():
        link_prop = links_data[key]

        to_node = _get_node(tree, link_prop["to_node"])
        input_socket = _get_socket(to_node, link_prop["to_socket"], "inputs")
        from_node = _get_node(tree, link_prop["from_node"])
        output_socket = _get_socket(from_node, link_prop["from_socket"], "outputs")
        if input_socket == None or output_socket == None:
            print(f'[{link_prop["from_node"]}]{link_prop["from_socket"]} -> [{link_prop["to_node"]}]{link_prop["to_socket"]} is link failed!')
            continue
        link = tree.links.new(input_socket, output_socket)
        links.append(link)

    return links

def _set_linestyles(render_layer_settings, load_path):
    """ FreeStyleのLineStyleの設定
        ※ViewLayerのLineSetの読み込みより先に行う
        (LineSetでLineStyleを使うので)

    Args:
        render_layer_settings (Dictionary): RenderLayerの設定
        load_path (str): 読み込むパス
    """
    if "linestyle_names" not in render_layer_settings:
        return

    props = bpy.context.scene.compositing_io
    
    # 既存のLineStyleをクリア
    if props.is_clear_freestyle:
        for ls in bpy.data.linestyles:
            bpy.data.linestyles.remove(ls)

    # LineStyleの読み込み
    # LineStyleは元データからAppend出来るので読み込み
    linestyle_names = render_layer_settings["linestyle_names"]
    for ls_name in linestyle_names:
        directory = load_path + DATA_FREESTYLE_LINESTYLE
        bpy.ops.wm.append(directory=directory, filename=ls_name, use_recursive=False)

def _set_view_layer_props(render_layer_settings):
    """ 各ViewLayer毎のプロパティを設定

    Args:
        render_layer_settings (Dictionary): RenderLayerの設定
    """
    props = bpy.context.scene.compositing_io

    render_layer_props = render_layer_settings["render_layer_props"]
    for name in render_layer_props.keys():
        vl_name = _calc_view_layer_name(name)
        vl = bpy.context.scene.view_layers[vl_name]
        rl_prop = render_layer_props[name]

        # Passes, Filter 設定
        vl_simple = rl_prop["vl_simple"]
        for prop in vl_simple:
            if not hasattr(vl, prop) or prop in ["cycles", "aovs"]:
                continue
            # 名前は書き換えない
            if prop == "name":
                continue
            setattr( vl, prop, vl_simple[prop] )

        # AOV 設定
        if hasattr(vl, "aovs"):
            # 2.93以降用
            for aov in [aov for aov in vl.aovs]:
                # print( "  --> ", len( vl.aovs ), aov )
                vl.active_aov_index = 0
            prop_aovs = rl_prop["aovs"]
            for prop in prop_aovs:
                # 追加済みは追加しない
                if prop["name"] in vl.aovs:
                    continue
                aov = vl.aovs.add()
                aov.name = prop["name"]
                aov.type = prop["type"]
        else:
            # 2.91以前用
            vl.cycles.aovs.clear()
            prop_aovs = rl_prop["aovs"]
            for prop in prop_aovs:
                # 追加済みは追加しない
                if prop["name"] in vl.cycles.aovs:
                    continue
                aov = vl.cycles.aovs.add()
                aov.name = prop["name"]
                aov.type = prop["type"]

        # FreeStyle 設定
        if not bpy.context.scene.render.use_freestyle:
            continue
        if not "free_style" in rl_prop:
            continue
        fs = rl_prop["free_style"]
        fs_simple = fs["fs_simple"]
        for fs_prop in fs_simple:
            if not hasattr(vl.freestyle_settings, fs_prop):
                continue
            setattr(vl.freestyle_settings, fs_prop, fs_simple[fs_prop])

        if not "linesets" in fs:
            continue

        # LineSetを生成するとLineStyleが自動で生成されるので生成前の一覧をキャッシュ
        cache_linestyles = [ls.name for ls in bpy.data.linestyles]

        # FreeStyleのLineSet設定
        linesets = fs["linesets"]
        if props.is_clear_freestyle and vl.freestyle_settings.linesets != None:
            for l in vl.freestyle_settings.linesets:
                vl.freestyle_settings.linesets.remove(l)
        for key in linesets.keys():
            ls = linesets[key]
            auto_props = ls["auto_props"]
            new_ls = vl.freestyle_settings.linesets.new(auto_props["name"])
            for p in auto_props:
                if not hasattr(new_ls, p):
                    continue
                setattr(new_ls, p, auto_props[p])

            # LineStyleの設定
            manual_props = ls["manual_props"]
            if manual_props["linestyle_name"] not in bpy.data.linestyles:
                continue
            new_ls.linestyle = bpy.data.linestyles[manual_props["linestyle_name"]]
            
        # 自動で生成されたLineStyleを削除
        for ls in bpy.data.linestyles:
            if ls.name in cache_linestyles:
                continue
            
            bpy.data.linestyles.remove(ls)

# -- Get --

def _get_node(tree, name):
    """ ノードを取得

    Args:
        tree (bpy.types.NodeTree): ノードツリー
        name (str): ノード名

    Returns:
        bpy.types.Node: ノード
    """
    nodes = [n for n in tree.nodes if n.name == name]
    if len(nodes) != 1:
        print(f"[{name}]のノード数が[{len(nodes)}]")
        return None

    return nodes[0]

def _get_socket(node, socket_name, io_prop_name):
    """ ソケットを取得

    Args:
        node (bpy.types.Node): ノード
        socket_name (str): ソケット名
        io_prop_name (str): 入出力のプロパティ名

    Returns:
        NodeSocket: ソケット
    """
    if not hasattr(node, io_prop_name):
        print(f"[{node}]に[{io_prop_name}]のプロパティがありません.")
        return None
    
    target_sockets = getattr(node, io_prop_name)
    
    # Rerouteの場合
    if node.bl_idname == "NodeReroute":
        for s in target_sockets:
            # 生成直後はidentifierがoutputだが、入力が入ると「output.001」に変わる
            # Rerouteのoutputは必ず1つなので、「.001」を除外して比較
            # identifier, socket_nameの大文字、小文字が生成時に変わっていることがあるので全て小文字に
            if str.lower(s.identifier.split(".")[0]) == str.lower(socket_name.split(".")[0]):
                return s
    else:
        sockets = [s for s in target_sockets if s.identifier == socket_name]
        if len(sockets) != 1:
            print(f"[{node.name}]の{io_prop_name}に[{socket_name}]が[{len(sockets)}]個")
            return None
        return sockets[0]