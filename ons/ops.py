#############################
## Onion Skinning Operators
#############################
import bpy
from bpy.types import Operator, PropertyGroup
import gpu
import bgl
from gpu_extras.batch import batch_for_shader

import numpy as np
from mathutils import Vector, Matrix

# ########################################################## #
# Data (stroring it in the object or scene doesnt work well) #
# ########################################################## #
shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
frame_data = dict([])
batches = dict([])
extern_data = dict([])

# ################ #
# Functions        #
# ################ #
def frame_get_set(_obj, frame):
    tmpobj = _obj

    # Setting the frame to get an accurate reading of the object on the selected frame
    scn = bpy.context.scene
    scn.frame_set(frame)

    # Getting the Depenency Graph and the evaluated object
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval = tmpobj.evaluated_get(depsgraph)
    
    # Making a new mesh from the object.
    mesh = eval.to_mesh()
    mesh.update()
    
    # Getting the object's world matrix
    mat = Matrix(_obj.matrix_world)
    
    # This moves the mesh by the object's world matrix, thus making everything global space. This is much faster than getting each vertex individually and doing a matrix multiplication on it
    mesh.transform(mat)
    mesh.update()
    
    # loop triangles are needed to properly draw the mesh on screen
    mesh.calc_loop_triangles()
    mesh.update()
    
    # Creating empties so that all of the verts and indices can be gathered all at once in the next step
    vertices = np.empty((len(mesh.vertices), 3), 'f')
    indices = np.empty((len(mesh.loop_triangles), 3), 'i')
    
    # Getting all of the vertices and incices all at once (from: https://docs.blender.org/api/current/gpu.html#mesh-with-random-vertex-colors)
    mesh.vertices.foreach_get(
        "co", np.reshape(vertices, len(mesh.vertices) * 3))
    mesh.loop_triangles.foreach_get(
        "vertices", np.reshape(indices, len(mesh.loop_triangles) * 3))
    
    args = [vertices, indices]
    
    return args


def set_to_active(_obj):
    # Sets the object that is being used for the onion skinning
    
    scn = bpy.context.scene
    
    clear_active()
    
    scn.anmx_data.onion_object = _obj.name

    bake_frames()
    make_batches()


def clear_active():
    # Clears the active object
    scn = bpy.context.scene
    name = scn.anmx_data.onion_object

    # Clears all the data needed to store onion skins on the previously selected object
    frame_data.clear()
    batches.clear()
    extern_data.clear()
    
    # Gets rid of the selected object
    scn.anmx_data.onion_object = ""


def make_batches():
    # Custom OSL shader could be set here
    scn = bpy.context.scene
    access = scn.anmx_data
    _obj = bpy.data.objects[access.onion_object]
    
    
    for key in frame_data:
        arg = frame_data[key]
        vertices = arg[0]
        indices = arg[1]
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        batches[key] = batch
        

def bake_frames():
    # Needs to do the following:
    # 1. Bake the data for every frame and store it in the objects "["frame_data"]" items
    scn = bpy.context.scene
    access = scn.anmx_data
    _obj = bpy.data.objects[access.onion_object]
    
    curr = scn.frame_current
    step = access.skin_step
    
    # Getting the first and last frame of the animation
    keyobj = _obj
    
    if _obj.parent is not None:
        keyobj = _obj.parent
        
    keyframes = []
    for fc in keyobj.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            keyframes.append(int(k.co[0]))
            
    keyframes = np.unique(keyframes)
    
    start = int(np.min(keyframes))
    end = int(np.max(keyframes)) + 1
    
    if access.onion_mode == "PF":
        for f in range(start, end):
            arg = frame_get_set(_obj, f)
            frame_data[str(f)] = arg
        extern_data.clear()
        
    elif access.onion_mode == "PFS":
        for f in range(start, end, step):
            arg = frame_get_set(_obj, f)
            frame_data[str(f)] = arg
        extern_data.clear()
        
    elif access.onion_mode == "DC":
        for fkey in keyframes:
            arg = frame_get_set(_obj, fkey)
            frame_data[str(fkey)] = arg
        extern_data.clear()
        
    elif access.onion_mode == "INB":
        for f in range(start, end):
            arg = frame_get_set(_obj, f)
            frame_data[str(f)] = arg
            
        extern_data.clear()
        for fkey in keyframes:
            extern_data[str(fkey)] = fkey
            
    
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
        
    modes = [("PF", "Per-Frame", "", 1), ("PFS", "Per-Frame Stepped", "", 2), ("DC", "Direct Keys", "", 3), ("INB", "Inbetweening", "", 4)]

    # Onion Skinning Properties
    skin_count: bpy.props.IntProperty(name="Count", default=1, min=1)
    skin_step: bpy.props.IntProperty(name="Step", default=1, min=1)
    onion_object: bpy.props.StringProperty(name="Onion Object", default="")
    onion_mode: bpy.props.EnumProperty(name="", get=None, set=None, items=modes)
    use_xray: bpy.props.BoolProperty(name="Use X-Ray", default=False)
    use_flat: bpy.props.BoolProperty(name="Flat Colors", default=False)
    toggle: bpy.props.BoolProperty(name="Draw", default=False, update=toggle_update)
    
    # Past settings
    past_color: bpy.props.FloatVectorProperty(name="Past Color", min=0, max=1, size=3, default=(1., .1, .1), subtype='COLOR')
    past_opacity_start: bpy.props.FloatProperty(name="Starting Opacity", min=0, max=1, default=0.5)
    past_opacity_end: bpy.props.FloatProperty(name="Ending Opacity", min=0, max=1, default=0.1)
    past_enabled: bpy.props.BoolProperty(name="Enabled?", default=True)
    
    # Future settings
    future_color: bpy.props.FloatVectorProperty(name="Future Color", min=0, max=1, size=3, default=(.1, .4, 1.), subtype='COLOR')
    future_opacity_start: bpy.props.FloatProperty(name="Starting Opacity", min=0, max=1, default=0.5)
    future_opacity_end: bpy.props.FloatProperty(name="Ending Opacity", min=0, max=1, default=0.1)
    future_enabled: bpy.props.BoolProperty(name="Enabled?", default=True)

  
# ################ #
# Operators        #
# ################ #


class ANMX_set_onion(Operator):
    bl_idname = "anim_extras.set_onion"
    bl_label = "Set Onion To Selected"    
    bl_description = "Sets the selected object to be the onion object"
    
    def execute(self, context):
        obj = context.active_object
    
        if obj == None:
            return {"CANCELLED"}
        
        if obj.parent is None:
            try:
                obj.animation_data.action.fcurves
            except AttributeError:
                    return {"CANCELLED"}
        else:
            try:
                obj.parent.animation_data.action.fcurves
            except AttributeError:
                    return {"CANCELLED"}
        
        if obj.type == 'MESH':
            set_to_active(obj)
    
        return {"FINISHED"}


class ANMX_clear_onion(Operator):
    bl_idname = "anim_extras.clear_onion"
    bl_label = "Clear Selected Onion"
    bl_description = "Clears the path of the onion object"
    
    def execute(self, context):
        clear_active()
    
        return {"FINISHED"}
    
    
class ANMX_update_onion(Operator):
    bl_idname = "anim_extras.update_onion"
    bl_label = "Update Selected Onion"
    bl_description = "Updates the path of the onion object"
    
    def execute(self, context):
        if context.active_object is None:
            return {"FINISHED"}
        
        if context.active_object.type == 'MESH':
            set_to_active(bpy.data.objects[context.scene.anmx_data.onion_object])
    
        return {"FINISHED"}

# Uses a list formatted in the following way to draw the meshes:
# [[vertices, indices, colors], [vertices, indices, colors]]
class ANMX_draw_meshes(Operator):
    bl_idname = "anim_extras.draw_meshes"
    bl_label = "Draw"
    bl_description = "Draws a set of meshes without creating objects"
    bl_options = {'REGISTER'}
    
    def __init__(self):
        self.handler = None
        self.timer = None
        self.mode = None

    def invoke(self, context, event):
        self.register_handlers(context)
        context.window_manager.modal_handler_add(self)
        self.mode = context.scene.anmx_data.onion_mode
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
        if context.scene.anmx_data.onion_object not in bpy.data.objects:
            self.unregister_handlers(context)
            return {'CANCELLED'}
        
        if context.scene.anmx_data.toggle is False or self.mode != context.scene.anmx_data.onion_mode:
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
                    bgl.glEnable(bgl.GL_BLEND)
                    bgl.glEnable(bgl.GL_CULL_FACE)
                if not ac.use_xray:
                    bgl.glEnable(bgl.GL_DEPTH_TEST)
                
                batches[key].draw(shader)
                
                bgl.glDisable(bgl.GL_BLEND)
                bgl.glDisable(bgl.GL_CULL_FACE)
                bgl.glDisable(bgl.GL_DEPTH_TEST)
                
            override = False
