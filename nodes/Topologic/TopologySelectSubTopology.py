import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

import importlib
importlib.import_module('topologicsverchok.nodes.Topologic.Replication')
from topologicsverchok.nodes.Topologic.Replication import flatten, repeat, onestep, iterate, trim, interlace, transposeList
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

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

def processItem(item, topologyType):
	topology = item[0]
	selector = item[1]
	t = 1
	if topologyType == "Vertex":
		t = 1
	elif topologyType == "Edge":
		t = 2
	elif topologyType == "Wire":
		t = 4
	elif topologyType == "Face":
		t = 8
	elif topologyType == "Shell":
		t = 16
	elif topologyType == "Cell":
		t = 32
	elif topologyType == "CellComplex":
		t = 64
	t = cppyy.gbl.int(t)
	return fixTopologyClass(topology.SelectSubtopology(selector, t))

topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7)]

class SvTopologySelectSubTopology(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the subtopology of the input Topology, of the specified type, closest to the input selector Vertex.    
	"""
	bl_idname = 'SvTopologySelectSubTopology'
	bl_label = 'Topology.SelectSubTopology'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	subtopologyType: EnumProperty(name="Subtopology Type", description="Specify subtopology type", default="Vertex", items=topologyTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Selector')
		self.outputs.new('SvStringsSocket', 'SubTopology')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "subtopologyType",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		selectorList = self.inputs['Selector'].sv_get(deepcopy=True)
		topologyList = flatten(topologyList)
		selectorList = flatten(selectorList)
		inputs = [topologyList, selectorList]
		outputs = []
		if ((self.Replication) == "Default"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		for anInput in inputs:
			outputs.append(processItem(anInput, self.subtopologyType))
		self.outputs['SubTopology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologySelectSubTopology)

def unregister():
	bpy.utils.unregister_class(SvTopologySelectSubTopology)
