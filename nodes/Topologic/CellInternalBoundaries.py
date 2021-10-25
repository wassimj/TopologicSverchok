import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	shells = []
	_ = item.InternalBoundaries(shells)
	return shells

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

class SvCellInternalBoundaries(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the internal boundaries (Shells) of the input Cell    
	"""
	bl_idname = 'SvCellInternalBoundaries'
	bl_label = 'Cell.InternalBoundaries'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cell')
		self.outputs.new('SvStringsSocket', 'Shells')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Cell'].sv_set([])
			return
		inputs = self.inputs['Cell'].sv_get(deepcopy=False)
		outputs = recur(inputs)
		if (len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['Shells'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellInternalBoundaries)

def unregister():
	bpy.utils.unregister_class(SvCellInternalBoundaries)
