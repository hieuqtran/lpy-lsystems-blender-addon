bl_info = {
    "name": "Lindenmaker",
    "description": "Lindenmayer systems for Blender via the L-Py framework.",
    "author": "Addon by Nikolaus Leopold. L-Py framework by Frederic Boudon et al.",
    "version": (1, 0),
    "blender": (2, 77, 0),
    "location": "View3D > Add > Mesh",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Add Mesh"
}

import lpy
from lindenmaker import turtle_interpretation
from lindenmaker.turtle_interpretation_error import TurtleInterpretationError
# reload scripts even if already imported, in case they have changed.
# this allows use of operator "Reload Scripts" (key F8)
import imp
imp.reload(lpy)
imp.reload(turtle_interpretation)

import bpy
import os.path
from math import radians
from mathutils import Vector, Matrix

class LindenmakerPanel(bpy.types.Panel):
    """Lindenmaker Panel"""
    bl_label = "Lindenmaker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = "Lindenmaker"
    
    # get text from open editor file
#    for area in bpy.context.screen.areas:
#        if area.type == 'TEXT_EDITOR':
#            text_editor = area.spaces.active
#            text = text_editor.text.as_string()
#    print(text)

    def draw(self, context):
        layout = self.layout
        
        layout.prop(context.scene, "lpyfile_path")
        
        col = layout.column() # if placed in column elements are closer to each other
        col.prop(context.scene, "turtle_step_size")
        col.prop(context.scene, "turtle_rotation_angle")
        
        col = layout.column()
        box = col.box()
        boxcol = box.column()
        boxcol.prop_search(context.scene, "internode_mesh_name", bpy.data, "meshes")
        boxcol.prop(context.scene, "turtle_line_width")
        boxcol.prop(context.scene, "turtle_width_growth_factor")
        boxcol.prop(context.scene, "internode_length_scale")
        boxsplit = boxcol.split(1/3)
        boxsplitcol1 = boxsplit.column()
        boxsplitcol1.prop(context.scene, "bool_draw_nodes")
        boxsplitcol2 = boxsplit.column()
        boxsplitcol2.enabled = context.scene.bool_draw_nodes
        boxsplitcol2.prop_search(context.scene, "node_mesh_name", bpy.data, "meshes", text="")
        boxcol.prop(context.scene, "bool_recreate_default_meshes")
        boxcolcol = boxcol.column()
        boxcolcol.enabled = context.scene.bool_recreate_default_meshes
        boxcolcol.prop(context.scene, "default_internode_cylinder_vertices")
        boxcolcol.prop(context.scene, "default_node_icosphere_subdivisions")
        
        col = layout.column()
        col.prop(context.scene, "bool_force_shade_flat")
        col.prop(context.scene, "bool_no_hierarchy")
        
        layout.operator(Lindenmaker.bl_idname, icon='OUTLINER_OB_MESH')
        
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "section_lstring_expanded",
            icon="TRIA_DOWN" if context.scene.section_lstring_expanded else "TRIA_RIGHT",
            icon_only=True, emboss=False)
        row.label(text="Manual L-string Configuration")
        if context.scene.section_lstring_expanded is True:
            box.prop(context.scene, "lstring", text="")


class Lindenmaker(bpy.types.Operator):
    """Generate a mesh via a Lindenmayer system""" # tooltip for menu items and buttons.
    bl_idname = "mesh.lindenmaker" # unique identifier for buttons and menu items to reference.
    bl_label = "Add Mesh via Lindenmayer System" # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'} # enable undo for the operator.

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        scene = context.scene
        
        bpy.ops.object.select_all(action='DESELECT')
        
        # clear scene (for debugging)
        if False: # delete all objects
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
        if True: # remove unused meshes
            for item in bpy.data.meshes:
                if item.users is 0:
                    bpy.data.meshes.remove(item)
        if False: # remove all materials (including ones currently used)
            for item in bpy.data.materials: 
                item.user_clear()
                bpy.data.materials.remove(item)
        
        # load L-Py framework lsystem specification file (.lpy) and derive lstring
        if not os.path.isfile(scene.lpyfile_path):
            self.report({'ERROR_INVALID_INPUT'}, "Input file does not exist! Select a valid file path in the Lindenmaker options panel in the tool shelf.\nFile not found: {}".format(scene.lpyfile_path))
            return {'CANCELLED'}
        lsys = lpy.Lsystem(scene.lpyfile_path)
        #print("LSYSTEM DEFINITION: {}".format(lsys.__str__()))
        derivedAxialTree = lsys.derive()
        scene.lstring = str(lsys.interpret(derivedAxialTree)) # apply "interpretation" / "homomorphism" production rules after derivation, if any are given. this is not the graphical interpretation
        #print("LSYSTEM DERIVATION RESULT: {}".format(context.scene.lstring))
        
        # interpret derived lstring via turtle graphics
        try: 
            turtle_interpretation.interpret(scene.lstring, scene.turtle_step_size, 
                                                           scene.turtle_line_width,
                                                           scene.turtle_width_growth_factor,
                                                           scene.turtle_rotation_angle,
                                                           default_materialindex=0)
        except TurtleInterpretationError as e:
            self.report({'ERROR_INVALID_INPUT'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(Lindenmaker.bl_idname, icon='PLUGIN')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(menu_func)
    
    bpy.types.Scene.lpyfile_path = bpy.props.StringProperty(
        name="L-Py File Path", 
        description="Path of .lpy file to be imported", 
        maxlen=1024, subtype='FILE_PATH')
    bpy.types.Scene.lstring = bpy.props.StringProperty(
        name="L-string", 
        description="The L-string resulting from the L-system derivation, to be used for graphical interpretation.")
        
    bpy.types.Scene.turtle_step_size = bpy.props.FloatProperty(
        name="Default Turtle Step Size", 
        description="Default length value for 'F' (move and draw) and 'f' (move) commands if no arguments given.",
        default=2.0, 
        min=0.05, 
        max=100.0)
    bpy.types.Scene.turtle_rotation_angle = bpy.props.FloatProperty(
        name="Default Turtle Rotation Angle", 
        description="Default angle for rotation commands if no argument given.",
        default=45.0, 
        min=0.0, 
        max=360.0)
        
    bpy.types.Scene.internode_mesh_name = bpy.props.StringProperty(
        name="Internode Mesh", 
        description="Name of mesh to be used for drawing internodes via the 'F' (move and draw) command",
        default="LindenmakerDefaultInternodeMesh")
    bpy.types.Scene.turtle_line_width = bpy.props.FloatProperty(
        name="Default Line Width", 
        description="Default width of internode and node objects drawn via 'F' (move and draw) command.",
        default=1.0, 
        min=0.01, 
        max=100.0)
    bpy.types.Scene.turtle_width_growth_factor = bpy.props.FloatProperty(
        name="Default Width Growth Factor", 
        description="Factor by which line width is multiplied via ';' (width increment) command. Also used for ','(width decrement) command as 1-(factor-1).", 
        default=1.05, 
        min=1, 
        max=100.0)
    bpy.types.Scene.internode_length_scale = bpy.props.FloatProperty(
        name="Internode Length Scale", 
        description="Factor by which move step size is multiplied to yield internode length. Used to allow internode length to deviate from step size.", 
        default=1.0,
        min=0.0)
    bpy.types.Scene.bool_draw_nodes = bpy.props.BoolProperty(
        name="Draw Nodes:", 
        description="Draw node objects at turtle position after each move command. Otherwise uses Empty objects if hierarchy is used.",
        default=False)
    bpy.types.Scene.node_mesh_name = bpy.props.StringProperty(
        name="Node Mesh", 
        description="Name of mesh to be used for drawing nodes",
        default="LindenmakerDefaultNodeMesh")
    bpy.types.Scene.bool_recreate_default_meshes = bpy.props.BoolProperty(
        name="Recreate Default Internode / Node Meshes",
        description="Recreate the default internode cylinder and node sphere meshes in case they were modified",
        default=False)
    bpy.types.Scene.default_internode_cylinder_vertices = bpy.props.IntProperty(
        name="Default Internode Cylinder Vertices", 
        default=5, 
        min=3, 
        max=64)
    bpy.types.Scene.default_node_icosphere_subdivisions = bpy.props.IntProperty(
        name="Default Node Icosphere Subdivisions", 
        default=1, 
        min=1, 
        max=5)
    bpy.types.Scene.bool_force_shade_flat = bpy.props.BoolProperty(
        name="Force Flat Shading",
        description="Use flat shading for all parts of the structure",
        default=False)
    bpy.types.Scene.bool_no_hierarchy = bpy.props.BoolProperty(
        name="Single Object (No Hierarchy, Faster)",
        description="Create a single object instead of a hierarchy tree of objects (faster)",
        default=True)
        
    # properties for UI functionality (like collapsible sections etc.)
    bpy.types.Scene.section_lstring_expanded = bpy.props.BoolProperty(default = False)
    
def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)
    
    del bpy.types.Scene.lpyfile_path
    del bpy.types.Scene.lstring
    
    del bpy.types.Scene.turtle_step_size
    del bpy.types.Scene.turtle_rotation_angle
    
    del bpy.types.Scene.internode_mesh_name
    del bpy.types.Scene.turtle_line_width
    del bpy.types.Scene.turtle_width_growth_factor
    del bpy.types.Scene.internode_length_scale
    del bpy.types.Scene.bool_draw_nodes
    del bpy.types.Scene.node_mesh_name
    del bpy.types.Scene.bool_recreate_default_meshes
    del bpy.types.Scene.default_internode_cylinder_vertices
    del bpy.types.Scene.default_node_icosphere_subdivisions
    
    del bpy.types.Scene.bool_force_shade_flat
    del bpy.types.Scene.bool_no_hierarchy
    
    del bpy.types.Scene.section_lstring_expanded

# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()
    