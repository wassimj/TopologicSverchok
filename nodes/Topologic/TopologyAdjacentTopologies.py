import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(topology):
	returnList = []
	if topology.Type() == topologic.Edge.Type():
		topologies = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		_ = topology.AdjacentEdges(topologies)
		returnList = list(topologies)
	if topology.Type() == topologic.Face.Type():
		topologies = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = topology.AdjacentFaces(topologies)
		returnList = list(topologies)
	if topology.Type() == topologic.Cell.Type():
		topologies = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		_ = topology.AdjacentCells(topologies)
		returnList = list(topologies)
	return returnList

class SvTopologyAdjacentTopologies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a list of Topologies that are adjacent to and of the same type as the input Topology
	"""
	bl_idname = 'SvTopologyAdjacentTopologies'
	bl_label = 'Topology.AdjacentTopologies'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Topologies')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topologies'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyAdjacentTopologies)

def unregister():
	bpy.utils.unregister_class(SvTopologyAdjacentTopologies)
