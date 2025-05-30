#######################
## Onion Skinning GUI
#######################

import bpy
from .ops import *


class ANMX_gui(bpy.types.Panel):
    """Panel for all Onion Skinning Operations"""
    bl_idname = 'VIEW3D_PT_animextras_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AnimExtras'
    bl_label = 'Onion Skinning'

    
    def draw(self, context):
        layout = self.layout
        access = context.scene.anmx_data
        # obj = context.object
        obj = context.active_object

        # Makes UI split like 2.8 no split factor 0.3 needed
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        # Makes sure the user can't do any operations when the onion object doesn't exist
        if not access.onion_group or len(access.onion_group) == 0:
            layout.operator("anim_extras.set_onion")
            return
        if context.selected_objects == []:
            layout.label(text="Nothing selected", icon='INFO')
            return
        # if not ((obj.type == 'MESH') and hasattr(obj.animation_data,"action") or (obj.type=='EMPTY')):
        #     layout.label(text="Update needs active object", icon='INFO')
            # return    
        else:
            row = layout.row(align=True)
            row.operator("anim_extras.update_onion", text="Update")
            row.operator("anim_extras.clear_onion", text="Clear Selected")
            layout.separator(factor=0.2)
        
        
        box = layout.box()
        box.label(text="Onion Group:")
        for item in access.onion_group:
            box.label(text=item.name, icon='OUTLINER_OB_MESH')
        
        col = layout.column()
        col.prop(access, "onion_mode", text="Method")
        
        modes = {"PFS", "INB"}
        # if not access.onion_mode in modes: #
        if access.onion_mode != "PFS":
            row = layout.row()
            row.prop(access, "skin_count", text="Amount")

        if access.onion_mode == "PFS":
            col = layout.column(align=True)
            col.prop(access, "skin_count", text="Amount")
            col.prop(access, "skin_step", text="Step")
        
        text = "Past"
        if access.onion_mode == "INB":
            text = "Inbetween Color"
        
        row = layout.row(align=True)
        box = row.box()
        col = box.column(align=True)
        past = col.row(align=True)
        icoPast = 'HIDE_OFF' if access.past_enabled else 'HIDE_ON'
        past.row().prop(access, "past_enabled", text='', icon=icoPast, emboss=False)
        past.row().label(text=text)
        col.prop(access, "past_color", text="")
        col.prop(access, "past_opacity_start", text="Start Opacity", slider=True)
        col.prop(access, "past_opacity_end", text="End Opacity", slider=True)        
        
        text = "Future"

        if access.onion_mode == "INB":
            text = "Direct Keying Color"
        
        box = row.box()
        col = box.column(align=True)
        fut = col.row(align=True)
        icoFut = 'HIDE_OFF' if access.future_enabled else 'HIDE_ON'
        fut.prop(access, "future_enabled", text='', icon=icoFut, emboss=False)
        fut.label(text=text)
        col.prop(access, "future_color", text="")
        col.prop(access, "future_opacity_start", text="Start Opacity", slider=True)
        col.prop(access, "future_opacity_end", text="End Opacity", slider=True)
        
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        layout.separator(factor=0.2)
        
        col = layout.column(heading="Options", align=True)
        col.prop(access, "use_xray")
        col.prop(access, "use_flat")
        col.prop(access, "in_front")
        
        layout.use_property_split = False
        layout.separator(factor=0.2)
        
        text = "Draw"
        if access.toggle:
            text = "Stop Drawing"
        icoOni = 'ONIONSKIN_OFF' if access.toggle else 'ONIONSKIN_ON'
        layout.prop(access, "toggle", text=text, toggle=True, icon=icoOni)