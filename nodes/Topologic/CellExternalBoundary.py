import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	return item.ExternalBoundary()

class SvCellExternalBoundary(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the external boundary (Shell) of the input Cell    
	"""
	bl_idname = 'SvCellExternalBoundary'
	bl_label = 'Cell.ExternalBoundary'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cell')
		self.outputs.new('SvStringsSocket', 'Shell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Shell'].sv_set([])
			return
		inputs = self.inputs['Cell'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Shell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellExternalBoundary)

def unregister():
	bpy.utils.unregister_class(SvCellExternalBoundary)
