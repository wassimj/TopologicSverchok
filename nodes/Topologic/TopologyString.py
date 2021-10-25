import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	return item.String()

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
		
class SvTopologyString(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the BREP string of the input Topology    
	"""
	bl_idname = 'SvTopologyString'
	bl_label = 'Topology.String'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'String')

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
		self.outputs['String'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyString)

def unregister():
	bpy.utils.unregister_class(SvTopologyString)
