import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	topologyCells = []
	cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
	_ = item.Cells(cells)
	for aCell in cells:
		topologyCells.append(aCell)
	return topologyCells

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output = recur(anItem)
	else:
		output = processItem(input)
	return output
		
class SvTopologyCells(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Cells of the input Topology    
	"""
	bl_idname = 'SvTopologyCells'
	bl_label = 'Topology.Cells'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Cells')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Cells'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			print(anInput)
			outputs.append(recur(anInput))
		self.outputs['Cells'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyCells)

def unregister():
	bpy.utils.unregister_class(SvTopologyCells)
