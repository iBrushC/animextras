# Updated
# - Panel layout > updated to match 2.8 styling
# - Added cleaner eye toggles for past and future
# - Icons to some buttons

# Added
# - Option to work with linked rigs > needs work InBetween as we need to target Parent rig
# - In Front option > show mesh in front of onion skinning
# - Shortcuts > for easier and faster workflow
# - Addon preferences so shortcuts can be customized
# - Panel feedback when nothings is selected or wrong object

# Fixed
# - Possibly old onion skinning when another file is openened
# - Linked rigs and local object/mesh also show onion skinning

# Ideas
# - Auto update when working on posing > could be handy? > need fedback from real animators
# - Added option to do multiple objects > this would need merge of objects, not sure will still work properly

##################
## Initiation
##################

bl_info = {
    "name": "AnimExtras",
    "author": "Andrew Combs, Rombout Versluijs, Sebastian Sarmiento",
    "version": (1, 1, 6),
    "blender": (4, 4, 3),
    "description": "True onion skinning",
    "category": "Animation",
    "wiki_url": "https://github.com/iBrushC/animextras",
	"tracker_url": "https://github.com/iBrushC/animextras/issues" 
}

import bpy
import rna_keymap_ui
from bpy.types import AddonPreferences

from .ons.gui import *
from .ons import ops
from .ons import registers


class ANMX_AddonPreferences(AddonPreferences):
    """ Preference Settings Addon Panel"""
    bl_idname = __name__
    bl_label = "Addon Preferences"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text = "Hotkeys:")
        col.label(text = "Do NOT remove hotkeys, disable them instead!")

        col.separator()
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        col.separator()
        km = kc.keymaps["3D View"]

        kmi = registers.get_hotkey_entry_item(km, "anim_extras.update_onion","EXECUTE","tab")
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text = "Update Onion Object")
            col.label(text = "restore hotkeys from interface tab")
        col.separator()
        
        kmi = registers.get_hotkey_entry_item(km, "anim_extras.toggle_onion","EXECUTE","tab")
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text = "Toggle Draw Onion")
            col.label(text = "restore hotkeys from interface tab")
        col.separator()
        
        kmi = registers.get_hotkey_entry_item(km, "anim_extras.add_clear_onion","EXECUTE","tab")
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text = "Add / Clear Onion Object")
            col.label(text = "restore hotkeys from interface tab")
        col.separator()


addon_keymaps = []
classes = [ANMX_gui, ANMX_data, ANMX_set_onion, ANMX_draw_meshes, ANMX_clear_onion, ANMX_toggle_onion, ANMX_update_onion, ANMX_add_clear_onion, ANMX_AddonPreferences]


@persistent
def ANMX_clear_handler(scene):
    ops.clear_active(clrRig=False)
    # bpy.ops.anim_extras.draw_meshes('INVOKE_DEFAULT')

def register():
    for c in classes:
        bpy.utils.register_class(c)
    
    bpy.types.Scene.anmx_data = bpy.props.PointerProperty(type=ANMX_data)
    bpy.app.handlers.load_pre.append(ANMX_clear_handler)
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")

    kmi = km.keymap_items.new("anim_extras.update_onion", "R", "PRESS", alt = True, shift = True)
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new("anim_extras.toggle_onion", "T", "PRESS", alt = True, shift = True)
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new("anim_extras.add_clear_onion", "C", "PRESS", alt = True, shift = True)
    addon_keymaps.append((km, kmi))


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    
    bpy.app.handlers.load_pre.remove(ANMX_clear_handler)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
