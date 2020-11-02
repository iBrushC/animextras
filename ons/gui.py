#######################
## Onion Skinning GUI
#######################
import bpy
from .ops import *


''' GUI '''
class ANMX_gui(bpy.types.Panel):
    """Panel for all MotionFX Operations"""
    bl_idname = 'VIEW3D_PT_animextras_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AnimExtras'
    bl_label = 'AnimExtras'


    def draw(self, context):
        layout = self.layout
        access = context.scene.anmx_data
        obj = context.object
        
        if access.onion_object == "":
            layout.operator("anim_extras.set_onion")
        else:
            row = layout.row(align=True)
            row.operator("anim_extras.update_onion", text="Update")
            row.operator("anim_extras.clear_onion", text="Clear Selected")
            
        
        if access.onion_object is "":
            return
        else:
            try:
                bpy.data.objects[access.onion_object]
            except KeyError:
                return
        
        col = layout.column()
        col.label(text="Current Onion Object: {}".format(access.onion_object))
        
        col.prop(access, "onion_mode")
        
        col.separator(factor=1)
        

        row = layout.row()
    
        row = row.split(factor=0.3)
        
        row.label(text="Amount:")
        row.prop(access, "skin_count", text="")
        
        if access.onion_mode == "PFS":
            row = layout.row()
    
            row = row.split(factor=0.3)
            
            row.label(text="Step:")
            row.prop(access, "skin_step", text="")
        
        row = layout.row(align=True)
        
        box = row.box()
        col = box.column(align=True)
        col.label(text="Past")
        col.prop(access, "past_color", text="")
        col.prop(access, "past_opacity_start", text="Start Opacity", slider=True)
        col.prop(access, "past_opacity_end", text="End Opacity", slider=True)
        col.prop(access, "past_enabled")
        
        box = row.box()
        col = box.column(align=True)
        col.label(text="Future")
        col.prop(access, "future_color", text="")
        col.prop(access, "future_opacity_start", text="Start Opacity", slider=True)
        col.prop(access, "future_opacity_end", text="End Opacity", slider=True)
        col.prop(access, "future_enabled")
        
        layout.separator(factor=1)
        
        layout.prop(access, "use_xray")
        layout.prop(access, "use_flat")
        
        layout.separator(factor=1)
        
        text = "Draw"
        if access.toggle:
            text = "Stop Drawing"
        layout.prop(access, "toggle", text=text, toggle=True)
