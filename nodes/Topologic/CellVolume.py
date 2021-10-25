import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	return topologic.CellUtility.Volume(item)

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
		
class SvCellVolume(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the volume of the input Cell    
	"""
	bl_idname = 'SvCellVolume'
	bl_label = 'Cell.Volume'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cell')
		self.outputs.new('SvStringsSocket', 'Volume')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Volume'].sv_set([0])
			return
		inputs = self.inputs['Cell'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Volume'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellVolume)

def unregister():
	bpy.utils.unregister_class(SvCellVolume)
