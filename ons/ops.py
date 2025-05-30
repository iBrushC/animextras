#############################
## Onion Skinning Operators
#############################

import bpy
from bpy.app.handlers import persistent
from bpy.types import Operator, PropertyGroup
import gpu
from gpu_extras.batch import batch_for_shader
import bmesh

import numpy as np
from mathutils import Vector, Matrix

# ########################################################## #
# Data (stroring it in the object or scene doesnt work well) #
# ########################################################## #

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
frame_data = dict([])
batches = dict([])
extern_data = dict([])

# ################ #
# Functions        #
# ################ #

def frame_get_set(_obj, frame):
    scn = bpy.context.scene

    # Set the frame to get the correct geometry
    scn.frame_set(frame)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval = _obj.evaluated_get(depsgraph)
    mesh = eval.to_mesh()
    mesh.update()

    mat = Matrix(_obj.matrix_world)
    mesh.transform(mat)
    mesh.update()
    mesh.calc_loop_triangles()
    mesh.update()

    vertices = np.empty((len(mesh.vertices), 3), 'f')
    indices = np.empty((len(mesh.loop_triangles), 3), 'i')

    mesh.vertices.foreach_get("co", np.reshape(vertices, len(mesh.vertices) * 3))
    mesh.loop_triangles.foreach_get("vertices", np.reshape(indices, len(mesh.loop_triangles) * 3))

    args = [vertices, indices]

    return args


def set_to_active():
    """ Sets the onion skinning group as the active source for baking/drawing """
    scn = bpy.context.scene
    anmx = scn.anmx_data

    # Clear all data
    frame_data.clear()
    batches.clear()
    extern_data.clear()

    group_objs = anmx.get_onion_group()
    if not group_objs:
        return


    # Bake and batch using the joined mesh
    bake_frames()
    make_batches()


def clear_active(clrRig):
    """ Clears all onion skinning data and the onion group """

    # Clear all the data needed to store onion skins
    frame_data.clear()
    batches.clear()
    extern_data.clear()

    # Clear the onion group
    scn = bpy.context.scene
    anmx = scn.anmx_data
    anmx.onion_group.clear()


def make_batches():
    # Custom OSL shader could be set here
    scn = bpy.context.scene
    anmx = scn.anmx_data
    group_objs = anmx.get_onion_group()
    if not group_objs:
        return
    
    _obj = join_meshes(group_objs)
    
    
    
    for key in frame_data:
        arg = frame_data[key]  # Dictionaries are used rather than lists or arrays so that frame numbers are a given
        vertices = arg[0]
        indices = arg[1]
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        batches[key] = batch

    bpy.data.objects.remove(_obj)

    
        

def bake_frames():
    scn = bpy.context.scene
    anmx = scn.anmx_data

    group_objs = anmx.get_onion_group()
    if not group_objs:
        return

    curr = scn.frame_current
    step = anmx.skin_step

    # Use the scene's frame range
    start = scn.frame_start
    end = scn.frame_end + 1

    frame_data.clear()
    extern_data.clear()

    if anmx.onion_mode == "PF":
        frames = range(start, end)
    elif anmx.onion_mode == "PFS":
        frames = range(start, end, step)
    elif anmx.onion_mode == "DC":
        # Optionally, collect keyframes from all objects and their armatures
        frames = set()
        for obj in group_objs:
            # Mesh keyframes
            if obj.animation_data and obj.animation_data.action:
                for fc in obj.animation_data.action.fcurves:
                    for k in fc.keyframe_points:
                        frames.add(int(k.co[0]))
            # Armature keyframes
            if obj.parent and obj.parent.type == 'ARMATURE':
                arm = obj.parent
                if arm.animation_data and arm.animation_data.action:
                    for fc in arm.animation_data.action.fcurves:
                        for k in fc.keyframe_points:
                            frames.add(int(k.co[0]))
        frames = sorted(frames) if frames else range(start, end)
    elif anmx.onion_mode == "INB":
        frames = range(start, end)
    else:
        frames = []

    for f in frames:
        scn.frame_set(f)
        _obj = join_meshes(group_objs)
        arg = frame_get_set(_obj, f)
        frame_data[str(f)] = arg
        bpy.data.objects.remove(_obj)

    scn.frame_set(curr)
    

# ################ #
# Properties       #
# ################ #


class ANMX_data(PropertyGroup):
    # Custom update function for the toggle
    def toggle_update(self, context):
        if self.toggle:
            bpy.ops.anim_extras.draw_meshes('INVOKE_DEFAULT')
        return

    def inFront(self, context):
        scn = bpy.context.scene
        # Set show_in_front for all objects in the onion group
        for item in self.onion_group:
            obj = bpy.data.objects.get(item.name)
            if obj:
                obj.show_in_front = self.in_front
        # Optionally, handle use_xray logic if needed
        if "use_xray" in scn["anmx_data"]:
            if scn["anmx_data"]["use_xray"]:
                scn["anmx_data"]["use_xray"] = False if scn["anmx_data"]["in_front"] else True
        return

    modes = [
        ("PF", "Per-Frame", "Shows the amount of frames in the future and past", 1), 
        ("PFS", "Per-Frame Stepped", "Shows the amount of frames in the future and past with option to step-over frames. This allows to see futher but still have a clear overview what is happening", 2), 
        ("DC", "Direct Keys", "Show onion only on inserted keys using amount as frame when keys are visible", 3), 
        ("INB", "Inbetweening", " Inbetweening, lets you see frames with direct keyframes in a different color than interpolated frames", 4)
        ]


    # Onion Skinning Properties
    skin_count: bpy.props.IntProperty(name="Count", description="Number of frames we see in past and future", default=1, min=1)
    skin_step: bpy.props.IntProperty(name="Step", description="Number of frames to skip in conjuction with Count", default=1, min=1)
    onion_mode: bpy.props.EnumProperty(name="", get=None, set=None, items=modes)
    use_xray: bpy.props.BoolProperty(name="Use X-Ray", description="Draws the onion visible through the object", default=False)
    use_flat: bpy.props.BoolProperty(name="Flat Colors", description="Colors while not use opacity showing 100% of the color", default=False)
    in_front: bpy.props.BoolProperty(name="In Front", description="Draws the selected object in front of the onion skinning", default=False, update=inFront)
    toggle: bpy.props.BoolProperty(name="Draw", description="Toggles onion skinning on or off", default=False, update=toggle_update)
    

    # Past settings
    past_color: bpy.props.FloatVectorProperty(name="Past Color", min=0, max=1, size=3, default=(1., .1, .1), subtype='COLOR')
    past_opacity_start: bpy.props.FloatProperty(name="Starting Opacity", min=0, max=1, precision=2, default=0.5)
    past_opacity_end: bpy.props.FloatProperty(name="Ending Opacity", min=0, max=1, precision=2, default=0.1)
    past_enabled: bpy.props.BoolProperty(name="Enabled?", default=True)
    
    # Future settings
    future_color: bpy.props.FloatVectorProperty(name="Future Color", min=0, max=1, size=3, default=(.1, .4, 1.), subtype='COLOR')
    future_opacity_start: bpy.props.FloatProperty(name="Starting Opacity", min=0, max=1,precision=2, default=0.5)
    future_opacity_end: bpy.props.FloatProperty(name="Ending Opacity", min=0, max=1,precision=2, default=0.1)
    future_enabled: bpy.props.BoolProperty(name="Enabled?", default=True)

    
    onion_group: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    # Helper to get the list of objects
    def get_onion_group(self):
        return [bpy.data.objects[item.name] for item in self.onion_group if item.name in bpy.data.objects]


# ################ #
# Operators        #
# ################ #

def check_selected(context):
    return any(obj.type == 'MESH' for obj in context.selected_objects)

class ANMX_set_onion(Operator):
    bl_idname = "anim_extras.set_onion"
    bl_label = "Set Onion Group"
    bl_description = "Set selected mesh objects as the onion skin group"

    def execute(self, context):
        access = context.scene.anmx_data
        access.onion_group.clear()
        # Track overrides for cleanup
        if not hasattr(access, "onion_overrides"):
            access.onion_overrides = []
        else:
            access.onion_overrides.clear()

        for obj in context.selected_objects:
            if obj.type == 'MESH':
                item = access.onion_group.add()
                item.name = obj.name
        if not access.onion_group:
            self.report({'WARNING'}, "No valid mesh objects selected.")
            return {'CANCELLED'}
        print("Onion group set with %d objects." % len(access.onion_group))
        return {'FINISHED'}

class ANMX_clear_onion(Operator):
    bl_idname = "anim_extras.clear_onion"
    bl_label = "Clear Onion Group"
    bl_description = "Clear the current onion skin group"

    def execute(self, context):
        access = context.scene.anmx_data
        access.onion_group.clear()
        return {'FINISHED'}
    
class ANMX_toggle_onion(Operator):
    """ Operator for toggling the onion object so we can shortcut it"""
    bl_idname = "anim_extras.toggle_onion"
    bl_label = "Toggle Onion"
    bl_description = "Toggles onion ON/OFF"
    bl_options = {'REGISTER', 'UNDO' }
    
    def execute(self, context):
        context.scene.anmx_data.toggle = False if context.scene.anmx_data.toggle else True
    
        return {"FINISHED"}

class ANMX_add_clear_onion(Operator):
    """ Toggle for clearing and adding"""
    bl_idname = "anim_extras.add_clear_onion"
    bl_label = "Add/Toggle Onion"
    bl_description = "Add/Toggles onion ON/OFF"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Extra check for the shortcuts
        if not check_selected(context):
            self.report({'INFO'}, "Onion needs animated active selection")
            return {'CANCELLED'}

        anmx = context.scene.anmx_data
        # Check if the onion group is empty
        if not anmx.onion_group or len(anmx.onion_group) == 0:
            bpy.ops.anim_extras.set_onion()
        else:
            bpy.ops.anim_extras.clear_onion()

        return {"FINISHED"}


class ANMX_update_onion(Operator):
    bl_idname = "anim_extras.update_onion"
    bl_label = "Update Onion Group"
    bl_description = "Updates the onion skinning data for the current group"
    bl_options = {'REGISTER', 'UNDO' }
    
    def execute(self, context):
        # Update the onion skinning data for the group
        # Save current mode and selection
        prev_mode = context.mode
        prev_selected = [obj for obj in context.selected_objects]
        prev_active = context.view_layer.objects.active

        # Switch to Object mode
        if prev_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Select all objects in the onion group
        anmx = context.scene.anmx_data
        group_objs = anmx.get_onion_group()
        bpy.ops.object.select_all(action='DESELECT')
        for obj in group_objs:
            obj.select_set(True)
        if group_objs:
            context.view_layer.objects.active = group_objs[0]

        # Run the update logic
        set_to_active()

        # Restore previous selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in prev_selected:
            obj.select_set(True)
        if prev_active:
            context.view_layer.objects.active = prev_active

        # Restore previous mode
        if prev_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=prev_mode)

        return {"FINISHED"}

# Uses a list formatted in the following way to draw the meshes:
# [[vertices, indices, colors], [vertices, indices, colors]]
class ANMX_draw_meshes(Operator):
    bl_idname = "anim_extras.draw_meshes"
    bl_label = "Draw"
    bl_description = "Draws a set of meshes without creating objects"
    bl_options = {'REGISTER', 'UNDO' }

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        self.handler = None
        self.timer = None
        self.mode = context.scene.anmx_data.onion_mode
        self.register_handlers(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def register_handlers(self, context):
        self.timer = context.window_manager.event_timer_add(0.1, window=context.window)
        self.handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (context,), 'WINDOW', 'POST_VIEW')

    def unregister_handlers(self, context):
        context.scene.anmx_data.toggle = False
        context.window_manager.event_timer_remove(self.timer)
        if self.handler != None:
            bpy.types.SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')
        self.handler = None

    def modal(self, context, event):
        anmx = context.scene.anmx_data
        # Cancel if the onion group is empty
        if not anmx.onion_group or len(anmx.onion_group) == 0:
            self.unregister_handlers(context)
            return {'CANCELLED'}

        if anmx.toggle is False or self.mode != anmx.onion_mode:
            self.unregister_handlers(context)
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    def finish(self, context):
        self.unregister_handlers(context)
        return {'FINISHED'}
    
    def draw_callback(self, context):
        scn = context.scene
        ac = scn.anmx_data
        f = scn.frame_current

        pc = ac.past_color
        fc = ac.future_color
        


        override = False
        
        color = (0, 0, 0, 0)
        
        threshold = ac.skin_count
        
        if context.space_data.overlay.show_overlays == False:
            return
        
        for key in batches:
            f_dif = abs(f-int(key))

            # Getting the color if the batch is in the past
        
            if len(extern_data) == 0:
                if f > int(key):
                    if ac.past_enabled:
                        color = (pc[0], pc[1], pc[2], ac.past_opacity_start-((ac.past_opacity_start-ac.past_opacity_end)/ac.skin_count) * f_dif)
                    else:
                        override = True
                # Getting the color if the batch is in the future
                else:
                    if ac.future_enabled:
                        color = (fc[0], fc[1], fc[2], ac.future_opacity_start-((ac.future_opacity_start-ac.future_opacity_end)/ac.skin_count) * f_dif)
                    else:
                        override = True
            else:
                if key in extern_data:
                    color = (fc[0], fc[1], fc[2], ac.future_opacity_start-((ac.future_opacity_start-ac.future_opacity_end)/ac.skin_count) * f_dif)
                else:
                    color = (pc[0], pc[1], pc[2], ac.past_opacity_start-((ac.past_opacity_start-ac.past_opacity_end)/ac.skin_count) * f_dif)
            
            # Only draws if the frame is not the current one, it is within the skin limits, and there has not been an override
            if f != int(key) and f_dif <= ac.skin_count and not override:
                shader.bind()
                shader.uniform_float("color", color)

                # Theres gotta be a better way to do this. Seems super inefficient
                if not ac.use_flat:
                    gpu.state.blend_set('ALPHA')
                    gpu.state.face_culling_set('BACK')
                if not ac.use_xray:
                    gpu.state.depth_test_set('LESS')

                batches[key].draw(shader)

                gpu.state.blend_set('NONE')
                gpu.state.face_culling_set('NONE')
                gpu.state.depth_test_set('NONE')
            override = False

def join_meshes(objs, name="OnionGroupTemp"):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for obj in objs:
        if obj.type != 'MESH':
            continue
        eval_obj = obj.evaluated_get(depsgraph)
        temp_mesh = eval_obj.to_mesh()
        temp_mesh.transform(obj.matrix_world)
        bmesh_temp = bmesh.new()
        bmesh_temp.from_mesh(temp_mesh)
        bm.from_mesh(temp_mesh)
        bmesh_temp.free()
        eval_obj.to_mesh_clear()

    bm.to_mesh(mesh)
    bm.free()
    temp_obj = bpy.data.objects.new(name, mesh)
    print("Joining %s objects into %s" % (len(objs), name))
    return temp_obj



