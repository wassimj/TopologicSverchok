import bpy
from bpy.props import FloatProperty, StringProperty
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
	if item:
		return item.CenterOfMass()
	else:
		return None


class SvTopologyCentroid(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Create a Vertex that represents the centroid of the vertices of the input Topology
	"""
	bl_idname = 'SvTopologyCentroid'
	bl_label = 'Topology.Centroid'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Centroid')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Centroid'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyCentroid)

def unregister():
	bpy.utils.unregister_class(SvTopologyCentroid)
