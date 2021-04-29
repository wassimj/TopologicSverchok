import bpy
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import cppyy
import time


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

def processItem(item):
	topology = None
	graph = item[0]
	vertexA = item[1]
	vertexB = item[2]
	vertexKey = item[3]
	edgeKey = item[4]
	topology = fixTopologyClass(graph.ShortestPath(vertexA, vertexB, vertexKey, edgeKey))
	return topology

def matchLengths(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

class SvGraphShortestPath(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Wire the represents the shortest path between the two input Graph Vertices
	"""
	bl_idname = 'SvGraphShortestPath'
	bl_label = 'Graph.ShortestPath'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Vertex A')
		self.inputs.new('SvStringsSocket', 'Vertex B')
		self.inputs.new('SvStringsSocket', 'Vertex Key')
		self.inputs.new('SvStringsSocket', 'Edge Key')
		self.outputs.new('SvStringsSocket', 'Wire')


	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		
		graphList = self.inputs['Graph'].sv_get(deepcopy=False)
		vertexAList = self.inputs['Vertex A'].sv_get(deepcopy=False)
		vertexBList = self.inputs['Vertex B'].sv_get(deepcopy=False)
		if not(self.inputs['Vertex Key'].is_linked):
			vertexKeyList = [""]
		else:
			vertexKeyList = self.inputs['Vertex Key'].sv_get(deepcopy=False)
		if not(self.inputs['Edge Key'].is_linked):
			edgeKeyList = [""]
		else:
			edgeKeyList = self.inputs['Edge Key'].sv_get(deepcopy=False)
		matchLengths([graphList, vertexAList, vertexBList, vertexKeyList, edgeKeyList])
		inputs = zip(graphList, vertexAList, vertexBList, vertexKeyList, edgeKeyList)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Wire'].sv_set(outputs)
		end = time.time()
		print("Graph.ShortestPath Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphShortestPath)

def unregister():
    bpy.utils.unregister_class(SvGraphShortestPath)
