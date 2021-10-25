import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import time

import importlib
importlib.import_module('topologicsverchok.nodes.Topologic.Replication')
from topologicsverchok.nodes.Topologic.Replication import flatten, repeat, onestep, iterate, trim, interlace, transposeList
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

def processItem(item):
	graph = item[0]
	vertexA = item[1]
	vertexB = item[2]
	timeLimit = item[3]
	paths = []
	_ = graph.AllPaths(vertexA, vertexB, True, timeLimit, paths)
	return paths


class SvGraphAllPaths(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs all the found Paths, within the allowed time limit in seconds, that connect the input Vertices within the input Graph
	"""
	bl_idname = 'SvGraphAllPaths'
	bl_label = 'Graph.AllPaths'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	TimeLimit: IntProperty(name="Time Limit", default=10, min=1, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Vertex A')
		self.inputs.new('SvStringsSocket', 'Vertex B')
		self.inputs.new('SvStringsSocket', 'Time Limit').prop_name="TimeLimit"
		self.outputs.new('SvStringsSocket', 'Paths')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		graphList = self.inputs['Graph'].sv_get(deepcopy=True)
		vertexAList = self.inputs['Vertex A'].sv_get(deepcopy=True)
		vertexBList = self.inputs['Vertex B'].sv_get(deepcopy=True)
		timeLimitList = self.inputs['Time Limit'].sv_get(deepcopy=True)
		graphList = flatten(graphList)
		vertexAList = flatten(vertexAList)
		vertexBList = flatten(vertexBList)
		timeLimitList = flatten(timeLimitList)
		inputs = [graphList, vertexAList, vertexBList, timeLimitList]
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
		self.outputs['Paths'].sv_set(outputs)
		end = time.time()
		print("Graph All Paths Operation consumed "+str(round(end - start,4))+" seconds")
def register():
    bpy.utils.register_class(SvGraphAllPaths)

def unregister():
    bpy.utils.unregister_class(SvGraphAllPaths)
