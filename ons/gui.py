#######################
## Onion Skinning GUI
#######################
import bpy
from .ops import *


class ANMX_gui(bpy.types.Panel):
    """Panel for all onion skinning Operations"""
    bl_idname = 'VIEW3D_PT_animextras_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AnimExtras'
    bl_label = 'Onion Skinning'

    
    # All functions for drawing the panel go in here
    # TODO:
    # -- Seperate different areas (which control toggleable areas) into seperate functions
    
    def draw(self, context):
        # All predefined variables
        layout = self.layout
        access = context.scene.anmx_data
        obj = context.object
        
        # Makes sure the user can't do any operations when the onion object doesn't exist
        if access.onion_object not in bpy.data.objects:
            layout.operator("anim_extras.set_onion")
            return
        else:
            row = layout.row(align=True)
            row.operator("anim_extras.update_onion", text="Update")
            row.operator("anim_extras.clear_onion", text="Clear Selected")
        
        # Top label for the onion object. This may be replaced with a list if support for multiple onion objects is added
        col = layout.column()
        col.label(text="Current Onion Object: {}".format(access.onion_object))
        
        # Dropdown menu for the onion mode
        col.prop(access, "onion_mode")
        col.separator(factor=1)
        
        # Area for changing the amount of onion skins
        row = layout.row()
        row = row.split(factor=0.3)
        row.label(text="Amount:")
        row.prop(access, "skin_count", text="")
        
        # Special exception for if the mode is Per-Frame-Stepped
        # TODO:
        # -- Make this better. This isn't a futureproof method, and should probably be expandable
        if access.onion_mode == "PFS":
            row = layout.row()
            row = row.split(factor=0.3)
            row.label(text="Step:")
            row.prop(access, "skin_step", text="")
        
        # Boxes for selecting the past and future onion skinning options
        
        text = "Past"  # A text variable is used so that the box labels can be changed (different modes require different settings)
        if access.onion_mode == "INB":
            text = "Inbetween Color"
        # Past box
        row = layout.row(align=True)
        box = row.box()
        col = box.column(align=True)
        col.label(text=text)
        col.prop(access, "past_color", text="")
        col.prop(access, "past_opacity_start", text="Start Opacity", slider=True)
        col.prop(access, "past_opacity_end", text="End Opacity", slider=True)
        col.prop(access, "past_enabled")
        
        
        text = "Future"  # See text = "Past"
        if access.onion_mode == "INB":
            text = "Direct Keying Color"
        # Future box
        box = row.box()
        col = box.column(align=True)
        col.label(text=text)
        col.prop(access, "future_color", text="")
        col.prop(access, "future_opacity_start", text="Start Opacity", slider=True)
        col.prop(access, "future_opacity_end", text="End Opacity", slider=True)
        col.prop(access, "future_enabled")
        
        layout.separator(factor=1)
        
        # Settings for xray and flat shading
        layout.prop(access, "use_xray")
        layout.prop(access, "use_flat")
        
        layout.separator(factor=1)
        
        # Drawing toggle button., variable is used to display status
        text = "Draw"
        if access.toggle:
            text = "Stop Drawing"
        layout.prop(access, "toggle", text=text, toggle=True)
