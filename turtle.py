import bpy
from math import radians
from mathutils import Vector, Matrix

from lindenmaker.turtle_interpretation_error import TurtleInterpretationError

class Turtle:
    
    def __init__(self, _linewidth, _materialindex):
        scene = bpy.context.scene
        # turtle state consists of a 4x4 matrix and some drawing attributes
        self.mat = Matrix()
        self.linewidth = _linewidth
        self.materialindex = _materialindex
        self.current_parent = None # parent of objects on current branch
        # stack to save and restore turtle state
        self.stack = []
        
        # get mesh to use to draw internodes (mesh reuse to save memory)
        default_internode_mesh_name = bpy.types.Scene.internode_mesh_name[1]['default']
        if scene.internode_mesh_name not in bpy.data.meshes.keys():
            # custom mesh not found, revert to default
            scene.internode_mesh_name = default_internode_mesh_name
            if default_internode_mesh_name not in bpy.data.meshes.keys():
                self.create_default_internode_mesh(scene.default_internode_cylinder_vertices)
        if scene.bool_recreate_default_meshes and default_internode_mesh_name in bpy.data.meshes.keys():
            # recreate default mesh on user request
            self.default_internode_mesh = bpy.data.meshes[default_internode_mesh_name]
            self.default_internode_mesh.user_clear() # also clears fake user
            self.default_internode_mesh.name = default_internode_mesh_name+".DEPRECATED"
            self.create_default_internode_mesh(scene.default_internode_cylinder_vertices)
            scene.internode_mesh_name = default_internode_mesh_name
        self.internode_mesh = bpy.data.meshes[scene.internode_mesh_name]
            
        # get mesh to used to draw nodes (mesh reuse to save memory)
        default_node_mesh_name = bpy.types.Scene.node_mesh_name[1]['default']
        if scene.node_mesh_name not in bpy.data.meshes.keys():
            # custom mesh not found, revert to default
            scene.node_mesh_name = default_node_mesh_name
            if default_node_mesh_name not in bpy.data.meshes.keys():
                self.create_default_node_mesh(scene.default_node_icosphere_subdivisions)
        if scene.bool_recreate_default_meshes and default_node_mesh_name in bpy.data.meshes.keys():
            # recreate default mesh on user request
            self.default_node_mesh = bpy.data.meshes[default_node_mesh_name]
            self.default_node_mesh.user_clear() # also clears fake user
            self.default_node_mesh.name = default_node_mesh_name+".DEPRECATED"
            self.create_default_node_mesh(scene.default_node_icosphere_subdivisions)
            scene.node_mesh_name = default_node_mesh_name
        self.node_mesh = bpy.data.meshes[scene.node_mesh_name]
        
        # init root node
        if bpy.context.scene.bool_no_hierarchy:
            # create empty mesh with no vertices to join with subsequent objects
            bpy.ops.mesh.primitive_plane_add()
            root = bpy.context.object
            root.data.name = "Root"
            root.data.use_auto_smooth = True
            root.data.auto_smooth_angle = radians(85)
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.select_all(action = 'SELECT')
            bpy.ops.mesh.delete()
            bpy.ops.object.mode_set(mode = 'OBJECT')
        else:
            bpy.ops.object.empty_add(type='ARROWS', radius=0)
        self.root = self.current_parent = bpy.context.object
        bpy.ops.object.select_all(action='DESELECT')
        
    def push(self):
        """Push turtle state to stack and place draw node object as parent for subsequent cylinders"""
        # push state to stack
        self.stack.append((self.mat.copy(), self.linewidth, self.materialindex, self.current_parent))
        if not bpy.context.scene.bool_no_hierarchy:
            if bpy.context.scene.bool_draw_nodes:
                # add node object as new parent for objects on this branch
                nodeobj = self.draw_node_module(scalefactor=self.linewidth)
                nodeobj.name = "Node"
                self.current_parent = nodeobj
            else:
                # add empty as new parent for objects on this branch
                bpy.ops.object.empty_add(type='ARROWS', radius=0)
                empty = bpy.context.object
                empty.name = "Node"
                empty.matrix_world *= self.mat
                self.add_child_to_current_branch_parent(empty)
                self.current_parent = empty 
                bpy.ops.object.select_all(action='DESELECT')
        elif bpy.context.scene.bool_draw_nodes:
            # just draw nodes without hierarchy
            self.draw_node_module(scalefactor=self.linewidth)
        
    def pop(self):
        """Pop last turtle state from stack and use as current"""
        (self.mat, self.linewidth, self.materialindex, self.current_parent) = self.stack.pop()

    def move(self, stepsize):
        """Move turtle in its heading direction."""
        vec = self.mat * Vector((stepsize,0,0,0))
        self.mat.col[3] += vec 
        
    def turn(self, angle_degrees):
        self.mat *= Matrix.Rotation(radians(angle_degrees), 4, 'Z')
    def pitch(self, angle_degrees):
        self.mat *= Matrix.Rotation(radians(angle_degrees), 4, 'Y')
    def roll(self, angle_degrees):
        self.mat *= Matrix.Rotation(radians(angle_degrees), 4, 'X')
        
    def draw_internode_module(self, length, width=None):
        """Draw internode object instance in current turtle coordinate system."""
        if width is None:
            width = self.linewidth
        scene = bpy.context.scene
        self.draw_module(self.internode_mesh, 
                         "Internode", 
                         scale=Vector((length*scene.internode_length_scale, width, width)),
                         assign_material_by_index=True)
                         
    def draw_node_module(self, scalefactor=1):
        """Draw node object instance in current turtle coordinate system."""
        return self.draw_module(self.node_mesh, 
                         "Node", 
                         scale=Vector((scalefactor, scalefactor, scalefactor)),
                         assign_material_by_index=True)
    
    def draw_module_from_custom_object(self, objname, objscale=Vector((1, 1, 1))):
        """Add custom object instance in current turtle coordinate system."""
        # get object data (mesh) for drawing
        # dont add material, object can be edited itself
        if objname not in bpy.data.objects.keys():
            raise TurtleInterpretationError("Error using '~' draw custom object command: No object named '{}'. Example usage: ~(\"Object\")".format(objname))
        self.draw_module(bpy.data.objects[objname].data, name=objname, scale=objscale)
    
    def draw_module(self, 
                    mesh, 
                    name="Module", 
                    scale=Vector((1, 1, 1)), 
                    assign_material_by_index=False):
        """Add object instance from given shared mesh in current turtle coordinate system."""
        scene = bpy.context.scene
        obj = bpy.data.objects.new(name, mesh) # create new object sharing the given mesh data
        scene.objects.link(obj)
        scene.objects.active = obj
        obj.select = True
        # optionally set shading
        if scene.bool_force_shade_flat:
            bpy.ops.object.shade_flat()
        else:
            bpy.ops.object.shade_smooth()
        # optionally create material slot and assign material from given materialindex
        # note: the important thing is to create a material slot for the module,
        # other materials can be assigned to it later
        if assign_material_by_index:
            # if materialindex exceeds length of material list just create new empty materials
            while self.materialindex >= len(bpy.data.materials): 
                bpy.ops.material.new()
            # to avoid cluttering the shared mesh, link material to current object
            # when joining objects (no hierarchy) relevant polygons will have the material assigned
            obj.active_material = bpy.data.materials[self.materialindex] # also adds slot if none
            obj.material_slots[0].link = 'OBJECT'
            obj.material_slots[0].material = bpy.data.materials[self.materialindex]
        # align object with turtle
        obj.matrix_world *= self.mat
        # set scale
        obj.scale = scale
        # add obj to existing structure
        if scene.bool_no_hierarchy:
            self.root.select = True
            scene.objects.active = self.root
            bpy.ops.object.join()
        else:
            self.add_child_to_current_branch_parent(obj)
        bpy.ops.object.select_all(action='DESELECT')
        
        if not bpy.context.scene.bool_no_hierarchy:
            return obj # return a reference to the object in case that is needed
        
    def add_child_to_current_branch_parent(self, object):
        if self.current_parent is None:
            return
        object.parent = self.current_parent
        object.matrix_parent_inverse = self.current_parent.matrix_world.inverted()
        
    def create_default_internode_mesh(self, vertex_count):
        """Initialize the default cylinder mesh used to draw internodes"""
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertex_count, radius=0.5)
        cyl = bpy.context.object
        # rotate cylinder mesh to point towards x axis and position origin at base
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.rotate(value=radians(90), axis=(0, 1, 0))
        bpy.ops.transform.translate(value=(1,0,0))
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        cyl.data.name = bpy.types.Scene.internode_mesh_name[1]['default']
        # smooth cylinder sides, but not cylinder caps
        cyl.data.use_auto_smooth = True
        cyl.data.auto_smooth_angle = radians(85)
        # delete object and make sure mesh will persist via fake user reference
        cyl.data.use_fake_user = True
        bpy.ops.object.delete()
        
    def create_default_node_mesh(self, _subdivisions=1):
        """Initialize the default icosphere mesh used to draw nodes"""
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=_subdivisions, size=0.5)
        icosphere = bpy.context.object
        icosphere.data.name = bpy.types.Scene.node_mesh_name[1]['default']
        icosphere.data.use_auto_smooth = True
        icosphere.data.auto_smooth_angle = radians(85)
        # delete object and make sure mesh will persist via fake user reference
        icosphere.data.use_fake_user = True
        bpy.ops.object.delete()
        