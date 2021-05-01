import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty
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
	return item.IsClosed()

class SvShellIsClosed(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the input Wire is closed. Outputs False otherwise   
	"""
	bl_idname = 'SvShellIsClosed'
	bl_label = 'Shell.IsClosed'
	Bool: BoolProperty(name="Bool", default=False, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Shell')
		self.outputs.new('SvStringsSocket', 'Is Closed').prop_name = 'Bool'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Is Closed'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvShellIsClosed)

def unregister():
	bpy.utils.unregister_class(SvShellIsClosed)
