import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import time

import importlib
importlib.import_module('topologicsverchok.nodes.Topologic.Replication')
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
from topologicsverchok.nodes.Topologic.Replication import flatten, repeat, onestep, iterate, trim, interlace, transposeList

def processItem(item):
	graph = item[0]
	vertexA = item[1]
	vertexB = item[2]
	tolerance = item[3]
	return graph.Edge(vertexA, vertexB, tolerance)

class SvGraphEdge(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Edge connecting the input Vertices within the input Graph
	"""
	bl_idname = 'SvGraphEdge'
	bl_label = 'Graph.Edge'
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, min=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Vertex A')
		self.inputs.new('SvStringsSocket', 'Vertex B')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Edge')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		graphList = self.inputs['Graph'].sv_get(deepcopy=True)
		vertexAList = self.inputs['Vertex A'].sv_get(deepcopy=True)
		vertexBList = self.inputs['Vertex B'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		graphList = flatten(graphList)
		vertexAList = flatten(vertexAList)
		vertexBList = flatten(vertexBList)
		toleranceList = flatten(toleranceList)
		inputs = [graphList, vertexAList, vertexBList, toleranceList]
		outputs = []
		if ((self.Replication) == "Default"):
			inputs = iterate(inputs)
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
			outputs.append(processItem(anInput))
		self.outputs['Edge'].sv_set(outputs)
		end = time.time()
		print("Graph Edge Operation consumed "+str(round(end - start,4))+" seconds")
def register():
    bpy.utils.register_class(SvGraphEdge)

def unregister():
    bpy.utils.unregister_class(SvGraphEdge)
