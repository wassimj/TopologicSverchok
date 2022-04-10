import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

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
	context = item
	topology = None
	try:
		topology = context.Topology()
	except:
		topology = None
	return topology

class SvContextTopology(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Topology of the input Context   
	"""
	bl_idname = 'SvContextTopology'
	bl_label = 'Context.Topology'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Context')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		contextList = self.inputs['Context'].sv_get(deepcopy=True)
		contextList = flatten(contextList)
		outputs = []
		for anInput in contextList:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvContextTopology)

def unregister():
    bpy.utils.unregister_class(SvContextTopology)
