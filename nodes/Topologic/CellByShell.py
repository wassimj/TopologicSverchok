import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

def processItem(item):
	return topologic.Cell.ByShell(item)

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem(input)
	return output

class SvCellByShell(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cell from the input Shell. The Shell has to be closed
	"""
	bl_idname = 'SvCellByShell'
	bl_label = 'Cell.ByShell'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Shell')
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		shellList = self.inputs['Shell'].sv_get(deepcopy=False)
		outputs = recur(shellList)
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellByShell)

def unregister():
	bpy.utils.unregister_class(SvCellByShell)
