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
![image](https://user-images.githubusercontent.com/1855970/152464442-26f39ab2-e1d3-4608-9f57-e45b10d9e742.png)

* LoadPath
  * The path to the Blender file to load.
* Delete current CompositingNodes
  * Deletes the currently configured node and then loads it.
* Delete current ViewLayers
  * Delete the currently set ViewLayer and then load it.
* Delete current LineSet, LineStyle
  * Delete the currently set LineSets and then load them.
  * If you do not delete the file, the new file will be added with the same name without overwriting the old one.
* Delete current NodeGroups
  * Delete the currently configured NodeGroups and then load them.
* Add ViewLayer Text
  * The character to be added to the head of the ViewLayer when loading.
* Load
  * Execute loading based on the above settings.

## Video
[![Watch on YouTube](https://img.youtube.com/vi/gwiI7nSzigI/0.jpg)](https://www.youtube.com/watch?v=gwiI7nSzigI)

## Install
You can install from [Tools:Q](https://github.com/Project-StudioQ/toolsq_common)

## License
This blender addon is under GNU Public License v2.
