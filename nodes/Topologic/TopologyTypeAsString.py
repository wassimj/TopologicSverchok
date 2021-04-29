import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	return str(item.GetTypeAsString())

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
		
class SvTopologyTypeAsString(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the BREP string of the input Topology    
	"""
	bl_idname = 'SvTopologyTypeAsString'
	bl_label = 'Topology.TypeAsString'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Type String')

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
		self.outputs['Type String'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyTypeAsString)

def unregister():
	bpy.utils.unregister_class(SvTopologyTypeAsString)
