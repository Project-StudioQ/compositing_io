# Tools:Q Common Compositing Loader

[日本語](README.md)

## Outline
Node Editor / All Mode

This is an add-on that reads Compositing-related settings from a specified Blender file.

Load the following settings.
* CompositingNode
* ViewLayer:LineSet,LineStyle
* ViewLayer:ShaderAOV

## Caution
* Some values may not be read by certain Compoisiting nodes.
* Layout > Frame may be misaligned.
  * Due to a bug in Blender itself, it is not possible to get the correct position. This may be fixed in the future.
  * [Remove node->offsetx/offsety [WIP]](https://developer.blender.org/D6540)

## UI
![image](https://user-images.githubusercontent.com/1855970/150478232-9836f8aa-dfc3-45ef-9159-55d28aea1d25.png)

* LoadPath
  * The path to the Blender file to load.
* 既存のノードを削除する？
  * Deletes the currently configured node and then loads it.
* 既存のViewLayerを削除する？
  * Delete the currently set ViewLayer and then load it.
* 既存のLineSetsを削除する？
  * Delete the currently set LineSets and then load them.
  * If you do not delete the file, the new file will be added with the same name without overwriting the old one.
* ViewLayerに追加する文字
  * The character to be added to the head of the ViewLayer when loading.
* Load
  * Execute loading based on the above settings.

## Video
[![Watch on YouTube](https://img.youtube.com/vi/gwiI7nSzigI/0.jpg)](https://www.youtube.com/watch?v=gwiI7nSzigI)

## Install
You can install from [Tools:Q](https://github.com/Project-StudioQ/toolsq_common)

## License
This blender addon is under GNU Public License v2.
