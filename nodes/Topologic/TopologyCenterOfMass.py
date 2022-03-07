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


class SvTopologyCenterOfMass(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Create a Vertex that represents the center of mass of the input Topology
	"""
	bl_idname = 'SvTopologyCenterOfMass'
	bl_label = 'Topology.CenterOfMass'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Center of Mass')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Center of Mass'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyCenterOfMass)

def unregister():
	bpy.utils.unregister_class(SvTopologyCenterOfMass)
