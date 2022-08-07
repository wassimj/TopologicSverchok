import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from mathutils import Matrix
from . import Replication

def processItem(item):
	dx, dy, dz = item
	return Matrix([[dx,0,0,0],
            [0,dy,0,0],
            [0,0,dz,0],
			[0,0,0,1]])

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]
		
class SvMatrixByScaling(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a Matrix based on the input scaling values    
	"""
	bl_idname = 'SvMatrixByScaling'
	bl_label = 'Matrix.ByScaling'
	X: FloatProperty(name="X", default=1, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=1, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=1, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.inputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.inputs.new('SvStringsSocket', 'Z').prop_name = 'Z'
		self.outputs.new('SvMatrixSocket', 'Matrix')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.separator()

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		xList = self.inputs['X'].sv_get(deepcopy=True)
		yList = self.inputs['Y'].sv_get(deepcopy=True)
		zList = self.inputs['Z'].sv_get(deepcopy=True)
		xList = Replication.flatten(xList)
		yList = Replication.flatten(yList)
		zList = Replication.flatten(zList)
		inputs = [xList, yList, zList]
		if ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = Replication.repeat(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(Replication.interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Matrix'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvMatrixByScaling)

def unregister():
	bpy.utils.unregister_class(SvMatrixByScaling)
