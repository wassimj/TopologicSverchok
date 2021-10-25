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

class SvFaceExternalBoundary(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the external boundary (Wire) of the input Face    
	"""
	bl_idname = 'SvFaceExternalBoundary'
	bl_label = 'Face.ExternalBoundary'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Wire')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Wire'].sv_set([])
			return
		inputs = self.inputs['Face'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Wire'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceExternalBoundary)

def unregister():
	bpy.utils.unregister_class(SvFaceExternalBoundary)
