##################
## Initiation
##################

bl_info = {
    "name": "AnimExtras",
    "author": "Andrew Combs",
    "version": (1, 0, 3),
    "blender": (2, 80, 0),
    "description": "True onion skinning",
    "category": "Animation"
}

import bpy
from .ons.gui import *
from .ons.ops import *

classes = [ANMX_gui, ANMX_data, ANMX_set_onion, ANMX_draw_meshes, ANMX_clear_onion, ANMX_update_onion]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    
    bpy.types.Scene.anmx_data = bpy.props.PointerProperty(type=ANMX_data)
    
    
def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    

if __name__ == "__main__":
    register()
