import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	return item.Dimensionality()

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
		
class SvTopologyDimensionality(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the dimensionality of the input Topology    
	"""
	bl_idname = 'SvTopologyDimensionality'
	bl_label = 'Topology.Dimensionality'
	dim: IntProperty(default=0, name='dim', update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Dimensionality').prop_name="dim"

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Cells'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Dimensionality'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyDimensionality)

def unregister():
	bpy.utils.unregister_class(SvTopologyDimensionality)
