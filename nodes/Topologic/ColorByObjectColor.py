import bpy
from bpy.props import EnumProperty, FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic
import math

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList




def processItem(bObject):
	color = bObject.color
	return (color[0],color[1], color[2], color[3])

class SvColorByObjectColor(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a color from the input Blender object color property   
	"""
	bl_idname = 'SvColorByObjectColor'
	bl_label = 'Color.ByObjectColor'

	def sv_init(self, context):
		#self.inputs[0].label = 'Auto'
		self.inputs.new('SvStringsSocket', 'Object')
		self.outputs.new('SvColorSocket', 'Color')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Object'].sv_get(deepcopy=True)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Color'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvColorByObjectColor)

def unregister():
    bpy.utils.unregister_class(SvColorByObjectColor)
