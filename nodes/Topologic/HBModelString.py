import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	return item.to_dict()

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
		
class SvHBModelString(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the HBJSON string of the input HB Model    
	"""
	bl_idname = 'SvHBModelString'
	bl_label = 'HBModel.String'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'HB Model')
		self.outputs.new('SvStringsSocket', 'String')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['String'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['String'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvHBModelString)

def unregister():
	bpy.utils.unregister_class(SvHBModelString)
