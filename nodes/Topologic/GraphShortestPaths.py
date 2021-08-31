import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import cppyy
import time

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

def nearestVertex(g, v, tol):
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	_ = g.Vertices(vertices)
	for aVertex in vertices:
		d = topologic.VertexUtility.Distance(v, aVertex)
		if d < tol:
			return aVertex
	return None

def isUnique(paths, wire):
	print(paths)
	if len(paths) < 1:
		print("Length of Paths less than 1 so returning True")
		return True
	for aPath in paths:
		print("Checking Path Uniqueness")
		print("aPath: " + str(aPath))
		print(wire)
		copyPath = fixTopologyClass(topologic.Topology.DeepCopy(aPath))
		dif = copyPath.Difference(wire, False)
		print(dif)
		if dif == None:
			print("Found path is NOT unique")
			return False
	print("Found a UNIQUE path!")
	return True

def processItem(item):
	graph = item[0]
	startVertex = item[1]
	endVertex = item[2]
	vertexKey = item[3]
	edgeKey = item[4]
	timeLimit = int(item[5])
	tolerance = item[6]
	
	shortestPaths = []
	start = time.time()
	end = time.time() + timeLimit
	while time.time() < end:
		gsv = nearestVertex(graph, startVertex, tolerance)
		gev = nearestVertex(graph, endVertex, tolerance)
		if (graph != None):
			wire = graph.ShortestPath(gsv,gev,vertexKey,edgeKey) # Find the first shortest path
			wireVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			flag = False
			try:
				_ = wire.Vertices(wireVertices)
				flag = True
			except:
				flag = False
			print(flag)
			print(wire)
			if (flag):
				print("Checking if wire is unique")
				#if(isUnique(shortestPaths, wire)):
					#shortestPaths.append(topologic.Topology.DeepCopy(wire))
					#print(shortestPaths)
			gtop = fixTopologyClass(graph.Topology())
			shortestPaths.append(gtop)
			#newWires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
			#_ = gtop.Wires(newWires)
			#newWires = list(newWires)
			#newWire = newWires[0]
			#print(newWire)
			#graph = topologic.Graph.ByTopology(newWire, True, False, False, False, False, False, tolerance)
			#print(graph)
	print(shortestPaths)
	return shortestPaths


class SvGraphShortestPaths(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a list of Wires that represents the shortest paths between the two input Graph Vertices found within the time limit in seconds
	"""
	bl_idname = 'SvGraphShortestPaths'
	bl_label = 'Graph.ShortestPaths'
	VertexKey: StringProperty(name='VertexKey', update=updateNode)
	EdgeKey: StringProperty(name='EdgeKey', update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	TimeLimit: IntProperty(name="Time Limit", default=10, min=1, update=updateNode)
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Vertex A')
		self.inputs.new('SvStringsSocket', 'Vertex B')
		self.inputs.new('SvStringsSocket', 'Vertex Key').prop_name='VertexKey'
		self.inputs.new('SvStringsSocket', 'Edge Key').prop_name='EdgeKey'
		self.inputs.new('SvStringsSocket', 'Time Limit').prop_name="TimeLimit"
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Wires')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		graphList = self.inputs['Graph'].sv_get(deepcopy=True)
		vertexAList = self.inputs['Vertex A'].sv_get(deepcopy=True)
		vertexBList = self.inputs['Vertex B'].sv_get(deepcopy=True)
		vertexKeyList = self.inputs['Vertex Key'].sv_get(deepcopy=True)
		edgeKeyList = self.inputs['Edge Key'].sv_get(deepcopy=True)
		timeLimitList = self.inputs['Time Limit'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tol'].sv_get(deepcopy=True)
		graphList = flatten(graphList)
		vertexAList = flatten(vertexAList)
		vertexBList = flatten(vertexBList)
		vertexKeyList = flatten(vertexKeyList)
		edgeKeyList = flatten(edgeKeyList)
		timeLimitList = flatten(timeLimitList)
		toleranceList = flatten(toleranceList)
		inputs = [graphList, vertexAList, vertexBList, vertexKeyList, edgeKeyList, timeLimitList, toleranceList]
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
			print("Graph.ShortestPaths: Sending to Processing")
			outputs.append(processItem(anInput))
		self.outputs['Wires'].sv_set(outputs)
		end = time.time()
		print("Graph ShortestPaths Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphShortestPaths)

def unregister():
    bpy.utils.unregister_class(SvGraphShortestPaths)
