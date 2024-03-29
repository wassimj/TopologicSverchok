import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	return [item.Type(), item.GetTypeAsString()]
		
class SvTopologyType(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Outputs the type of the input Topology as an integer ID and a string Name
	"""
	bl_idname = 'SvTopologyType'
	bl_label = 'Topology.Type'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'ID')
		self.outputs.new('SvStringsSocket', 'Name')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Cells'].sv_set([])
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		topologyList = flatten(topologyList)
		ids = []
		names = []
		for anInput in topologyList:
			output = processItem(anInput)
			ids.append(output[0])
			names.append(output[1])
		self.outputs['ID'].sv_set(ids)
		self.outputs['Name'].sv_set(names)

def register():
	bpy.utils.register_class(SvTopologyType)

def unregister():
	bpy.utils.unregister_class(SvTopologyType)
