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

# External data
# Can't be stored in scene or object data because dictionaries aren't supported
shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
frame_data = dict([])
batches = dict([])
extern_data = dict([])

# Functions
def frame_get_set(_obj, frame):
	# Gets all of the data from a mesh on a certain frame
    tmpobj = _obj

    # Setting the frame to get an accurate reading of the object on the selected frame
    scn = bpy.context.scene
    scn.frame_set(frame)

    # Applying the Depenency Graph (applying all modifiers) and getting the mesh
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval = tmpobj.evaluated_get(depsgraph)
    mesh = eval.to_mesh()
    mesh.update()
    
    # Transforming the mesh by its world matrix (does the equivalent of applying transforms) so that the meshes can all be in world space.
    mat = Matrix(_obj.matrix_world)
    mesh.transform(mat)
    mesh.update()
    
    # loop triangles are needed to properly draw the mesh and its faces on screen
    mesh.calc_loop_triangles()
    mesh.update()
    
    # Creating empties so that all of the verts and indices can be gathered all at once in the next step
    vertices = np.empty((len(mesh.vertices), 3), 'f')
    indices = np.empty((len(mesh.loop_triangles), 3), 'i')
    
    # Getting all of the vertices and incices all at once (from: https://docs.blender.org/api/current/gpu.html#mesh-with-random-vertex-colors)
    # There is no way that this script would be possible without this
    mesh.vertices.foreach_get(
        "co", np.reshape(vertices, len(mesh.vertices) * 3))
    mesh.loop_triangles.foreach_get(
        "vertices", np.reshape(indices, len(mesh.loop_triangles) * 3))
    
    args = [vertices, indices]
    
    return args


def set_to_active(_obj):
    # Sets the object that is being used for the onion skinning
    
    scn = bpy.context.scene
    
    # Clears the onion object, sets it to active and sets the frames and batches
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
    # Creates all the batches needed for drawing. All frames are calculated, then only certain ones are drawn.
    scn = bpy.context.scene
    access = scn.anmx_data
    _obj = bpy.data.objects[access.onion_object]
    
    # For every key(frame) in the calculated frame data it creates a batch with a shader that can be drawn in a single call.
    # TODO:
    # -- See if its possible to combine all frames into a single batch
    for key in frame_data:
        arg = frame_data[key]  # Dictionaries are used rather than lists or arrays so that frame numbers are a given
        vertices = arg[0]
        indices = arg[1]
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        batches[key] = batch
        

def bake_frames():
    # Goes through every single (necessary) frame and gets the object's data
    scn = bpy.context.scene
    access = scn.anmx_data
    _obj = bpy.data.objects[access.onion_object]
    
    # Reset value
    curr = scn.frame_current
    step = access.skin_step
    
    # Getting the first and last frame that there is animation data on either the object or its parent object
    # Makes sure that there are no unnecessary frames that are calculated and speeds up the script
    # TODO:
    # -- Fix random bugs with odd numbers
    # -- Allow for a custom keyobj (linked rigs do not work)
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
    
    # Different modes need to collect frames in different ways, which is done here
    # TODO:
    # -- Make this more streamlined and expandable, maybe using a scene EnumProperty
    if access.onion_mode == "PF":
        # Per-Frame
        for f in range(start, end):
            arg = frame_get_set(_obj, f)
            frame_data[str(f)] = arg
        extern_data.clear()
        
    elif access.onion_mode == "PFS":
        # Per-Frame-Stepped
        for f in range(start, end, step):
            arg = frame_get_set(_obj, f)
            frame_data[str(f)] = arg
        extern_data.clear()
        
    elif access.onion_mode == "DC":
        # Direct Keys
        for fkey in keyframes:
            arg = frame_get_set(_obj, fkey)
            frame_data[str(fkey)] = arg
        extern_data.clear()
        
    elif access.onion_mode == "INB":
        # Inbetweening
        for f in range(start, end):
            arg = frame_get_set(_obj, f)
            frame_data[str(f)] = arg
            
        extern_data.clear()
        for fkey in keyframes:
            extern_data[str(fkey)] = fkey
            
    
    scn.frame_set(curr)
    

# Properties
class ANMX_data(PropertyGroup):
    # Custom update function for the toggle
    def toggle_update(self, context):
        if self.toggle:
            bpy.ops.anim_extras.draw_meshes('INVOKE_DEFAULT')
        return
    
    # All the different modes are stored here
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


# Operators
# Most of these are just shells for existing functions, so optimizations are definitely possible
# P.S. "ANMX" is used as a prefix for any operators used in animation extras. This will probably change to "OS" when PathTools is added
class ANMX_set_onion(Operator):
    # Operator for setting the onion object
    bl_idname = "anim_extras.set_onion"
    bl_label = "Set Onion To Selected"    
    bl_description = "Sets the selected object to be the onion object"
    
    def execute(self, context):
        obj = context.active_object
        
        # Tons of error checks to make sure the script can't mess itself up
        if obj == None:
            return {"CANCELLED"}
        
        # Checks to make sure the object actually has animation
        # TODO:
        # -- Find a way to get rid of AttributeError try/except functions
        if obj.parent is None:
            try:
                obj.animation_data.action.fcurves
            except AttributeError:
                    return {"CANCELLED"}
        else:
            try:
                # This right here needs to change for allowing linked rigs
                obj.parent.animation_data.action.fcurves
            except AttributeError:
                    return {"CANCELLED"}
        
        # Makes sure the object is actually a mesh
        if obj.type == 'MESH':
            set_to_active(obj)
    
        return {"FINISHED"}


class ANMX_clear_onion(Operator):
    # Operator for clearing the onion object
    # This seems unnecessary
    bl_idname = "anim_extras.clear_onion"
    bl_label = "Clear Selected Onion"
    bl_description = "Clears the path of the onion object"
   
    def execute(self, context):
        clear_active()
        return {"FINISHED"}
    
    
class ANMX_update_onion(Operator):
    # Operator for updating the onion object
    bl_idname = "anim_extras.update_onion"
    bl_label = "Update Selected Onion"
    bl_description = "Updates the path of the onion object"
    
    def execute(self, context):
        if context.scene.anmx_data.onion_object in bpy.data.objects:
            set_to_active(bpy.data.objects[context.scene.anmx_data.onion_object])
    
        return {"FINISHED"}

# Uses a list formatted in the following way to draw the meshes:
# [[vertices, indices, colors], [vertices, indices, colors]]
class ANMX_draw_meshes(Operator):
    # Operator for actually drawing the meshes. Most of this was learned from https://www.youtube.com/user/jayanamgames
    bl_idname = "anim_extras.draw_meshes"
    bl_label = "Draw"
    bl_description = "Draws a set of meshes without creating objects"
    bl_options = {'REGISTER'}
    
    def __init__(self):
        self.handler = None
        self.timer = None
        self.mode = None
    
    # What happens when the operation is first invoked. Addes the modal handler and registers it with a timer
    def invoke(self, context, event):
        self.register_handlers(context)
        context.window_manager.modal_handler_add(self)
        self.mode = context.scene.anmx_data.onion_mode
        return {'RUNNING_MODAL'}
    # For some reason this needs a timer
    def register_handlers(self, context):
        self.timer = context.window_manager.event_timer_add(0.1, window=context.window)
        self.handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (context,), 'WINDOW', 'POST_VIEW')
    # gets rid of the draw handler and timer
    def unregister_handlers(self, context):
        context.scene.anmx_data.toggle = False
        context.window_manager.event_timer_remove(self.timer)
        if self.handler != None:
            bpy.types.SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')
        self.handler = None
    # Runs in the background to allow the operator to be stopped
    def modal(self, context, event):
        if context.scene.anmx_data.onion_object not in bpy.data.objects:
            self.unregister_handlers(context)
            return {'CANCELLED'}
        if context.scene.anmx_data.toggle is False or self.mode != context.scene.anmx_data.onion_mode:
            self.unregister_handlers(context)
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    # Gets rid of the handlers when finished.
    def finish(self, context):
        self.unregister_handlers(context)
        return {'FINISHED'}
    
    # The main drawing code
    def draw_callback(self, context):
        # Drawing callback that determines how everything should be drawn
        scn = context.scene
        ac = scn.anmx_data
        f = scn.frame_current
        pc = ac.past_color
        fc = ac.future_color
        
        override = False
        color = (0, 0, 0, 0)
        threshold = ac.skin_count
        
        # Doesnt draw if viewport overlays are off
        if context.space_data.overlay.show_overlays == False:
            return
        
        # Draws each batch inside the batches, the "key" variable is the frame that that batch is on
        # TODO:
        # -- Make it not a complete mess
        # -- Simplify color sampling
        # -- Try to reduce the number of if/else statements
        for key in batches:
            f_dif = abs(f-int(key))
            
            # The extern data determines how the colors are drawn. If the length isn't zero, inbetweening is active; otherwise, normal color sampling is active
            # TODO:
            # -- See if this can be done through a shader. (Note: would require custom GL batches to store which frame the mesh was stored on)
            if len(extern_data) == 0:
                # Standard color sampling
                # Getting the color if the batch is in the past
                if f > int(key):
                    if ac.past_enabled:
                        color = (pc[0], pc[1], pc[2], ac.past_opacity_start-((ac.past_opacity_start-ac.past_opacity_end)/ac.skin_count) * f_dif)  # This is horrible
                    else:
                        override = True
                # Getting the color if the batch is in the future
                else:
                    if ac.future_enabled:
                        color = (fc[0], fc[1], fc[2], ac.future_opacity_start-((ac.future_opacity_start-ac.future_opacity_end)/ac.skin_count) * f_dif)
                    else:
                        override = True
            else:
                # Inbetweening color sampling
                # If the key is a direct key it is drawn with the future color, otherwise its drawn with the past color
                if key in extern_data:
                    color = (fc[0], fc[1], fc[2], ac.future_opacity_start-((ac.future_opacity_start-ac.future_opacity_end)/ac.skin_count) * f_dif)
                else:
                    color = (pc[0], pc[1], pc[2], ac.past_opacity_start-((ac.past_opacity_start-ac.past_opacity_end)/ac.skin_count) * f_dif)
            
            # Only draws if the frame is not the current one, it is within the skin limits, and there has not been an override. This could definitely be done with a shader.
            if f != int(key) and f_dif <= ac.skin_count and not override:
                # Shader is finally bound using the defined color
                shader.bind()
                shader.uniform_float("color", color)
                
                # This seems inefficient, but nothing works properly without it.
                if not ac.use_flat:
                    bgl.glEnable(bgl.GL_BLEND)
                    bgl.glEnable(bgl.GL_CULL_FACE)
                if not ac.use_xray:
                    bgl.glEnable(bgl.GL_DEPTH_TEST)
                
                batches[key].draw(shader)
                
                bgl.glDisable(bgl.GL_BLEND)
                bgl.glDisable(bgl.GL_CULL_FACE)
                bgl.glDisable(bgl.GL_DEPTH_TEST)
            
            # Resets the override
            override = False
