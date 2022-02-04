# Tools:Q Common Compositing Loader

[English](README.en.md)

## 概要
Node Editor / All Mode

指定したBlenderファイルからCompositing関連設定の読み込みを行うアドオンです。

以下の設定を読み込みます。
* Compositingノード
* ViewLayerのLineSet,LineStyle
* ViewLayerのShaderAOV

## 注意
* 特定のCompoisitingノードでは値が一部読み込まれない可能性があります。
* Layout > Frameは位置がズレる可能性があります。
  * Blender自体の不具合により正常な位置を取得出来ない状態です。今後修正される可能性があります。
  * [Remove node->offsetx/offsety [WIP]](https://developer.blender.org/D6540)

## UI
![image](https://user-images.githubusercontent.com/1855970/150478232-9836f8aa-dfc3-45ef-9159-55d28aea1d25.png)

* LoadPath
  * 読み込みを行うBlenderファイルのパス。
* Delete current CompositingNodes
  * 現在設定されているノードを削除してから読み込みます。
* "Delete current ViewLayers
  * 現在設定されているViewLayerを削除してから読み込みます。
* Delete current LineSet, LineStyle
  * 現在設定されているLineSetsを削除してから読み込みます。
  * ※削除しない場合は同一名でも上書きせず同一名で新規追加されます。
* Delete current NodeGroups
  * 現在設定されているNodeGroupsを削除してから読み込みます。
* Add ViewLayer Text
  * 読み込み時にViewLayerの頭に追加する文字です。
* Load
  * 上記設定を元に読み込みを実行します。

## 動画
[![YouTubeで見る](https://img.youtube.com/vi/gwiI7nSzigI/0.jpg)](https://www.youtube.com/watch?v=gwiI7nSzigI)

## インストール
Project Studio Qが公開している [Tools:Q](https://github.com/Project-StudioQ/toolsq_common) よりインストールしてください。

## ライセンス
このBlenderアドオンは GNU Public License v2 です。
