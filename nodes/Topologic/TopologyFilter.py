import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
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

def classByType(argument):
	switcher = {
		1: Vertex,
		2: Edge,
		4: Wire,
		8: Face,
		16: Shell,
		32: Cell,
		64: CellComplex,
		128: Cluster }
	return switcher.get(argument, Topology)

def fixTopologyClass(topology):
  topology.__class__ = classByType(topology.GetType())
  return topology

def processItem(topologies, topologyType):
	filteredTopologies = []
	for aTopology in topologies:
		if aTopology.GetTypeAsString() == topologyType:
			filteredTopologies.append(aTopology)
	return filteredTopologies

topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7), ("Cluster", "Cluster", "", 8)]

class SvTopologyFilter(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Filters the input list of Topologies based on the input Topology type filter    
	"""
	bl_idname = 'SvTopologyFilter'
	bl_label = 'Topology.Filter'
	topologyType: EnumProperty(name="Topology Type", description="Specify topology type", default="Vertex", items=topologyTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topologies')
		self.outputs.new('SvStringsSocket', 'Topologies')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, "topologyType",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topologies'].sv_set([])
			return
		inputs = self.inputs['Topologies'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = processItem(inputs, self.topologyType)
		self.outputs['Topologies'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyFilter)

def unregister():
	bpy.utils.unregister_class(SvTopologyFilter)
