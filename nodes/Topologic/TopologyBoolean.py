import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
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

def getValueAtKey(dict, key):
	returnValue = None
	try:
		returnValue = (cppyy.bind_object(dict.ValueAtKey(key).Value(), "std::string"))
	except:
		returnValue = None
	return returnValue

def relevantSelector(topology):
	returnVertex = None
	if topology.GetType() == topologic.Vertex.Type():
		return topology
	elif topology.GetType() == topologic.Edge.Type():
		return topologic.EdgeUtility.PointAtParameter(topology, 0.5)
	elif topology.GetType() == topologic.Face.Type():
		return topologic.FaceUtility.InternalVertex(topology)
	elif topology.GetType() == topologic.Cell.Type():
		return topologic.CellUtility.InternalVertex(topology)
	else:
		return topology.Centroid()

def topologyContains(topology, vertex, tol):
	contains = False
	if topology.GetType() == topologic.Vertex.Type():
		print("topologyContains: Vertex")
		try:
			contains = (topologic.VertexUtility.Distance(sourceVertex, vertex) <= tol)
		except:
			contains = False
		return contains
	elif topology.GetType() == topologic.Edge.Type():
		print("topologyContains: Edge")
		try:
			_ = topologic.EdgeUtility.ParameterAtPoint(topology, vertex)
			contains = True
		except:
			contains = False
		return contains
	elif topology.GetType() == topologic.Face.Type():
		print("topologyContains: Face")
		return topologic.FaceUtility.IsInside(topology, vertex, tol)
	elif topology.GetType() == topologic.Cell.Type():
		print("topologyContains: Cell")
		return (topologic.CellUtility.Contains(topology, vertex, tol) == 0)
	return False

def transferDictionaries(sources, sinks, tol):
	print("Transfer Dictionaries: STEP 1")
	print(str(len(sources))+" sources and "+str(len(sinks))+" sinks")
	for sink in sinks:
		sinkKeys = []
		sinkValues = []
		iv = relevantSelector(sink)
		j = 1
		for source in sources:
			if topologyContains(source, iv, tol):
				d = source.GetDictionary()
				stl_keys = d.Keys()
				if len(stl_keys) > 0:
					copyKeys = stl_keys.__class__(stl_keys) #wlav suggested workaround. Make a copy first
					sourceKeys = [str((copyKeys.front(), copyKeys.pop_front())[0]) for x in copyKeys]
					for aSourceKey in sourceKeys:
						if aSourceKey not in sinkKeys:
							sinkKeys.append(aSourceKey)
							sinkValues.append("")
					for i in range(len(sourceKeys)):
						index = sinkKeys.index(sourceKeys[i])
						k = cppyy.gbl.std.string(sourceKeys[i])
						sourceValue = getValueAtKey(d, k)
						if sourceValue != None:
							if sinkValues[index] != "":
								sinkValues[index] = sinkValues[index]+","+sourceValue
							else:
								sinkValues[index] = sourceValue
		if len(sinkKeys) > 0 and len(sinkValues) > 0:
			stlKeys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
			for aKey in sinkKeys:
				stlKeys.push_back(aKey)
			stlValues = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
			for aValue in sinkValues:
				stlValues.push_back(topologic.StringAttribute(aValue))
			newDict = topologic.Dictionary.ByKeysValues(stlKeys, stlValues)
			_ = sink.SetDictionary(newDict)

def highestDimension(topology):
	if (topology.GetType() == topologic.Cluster.Type()):
		cellComplexes = cppyy.gbl.std.list[topologic.CellComplex.Ptr]()
		_ = topology.CellComplexes(cellComplexes)
		if len(cellComplexes) > 0:
			return topologic.CellComplex.Type()
		cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		_ = topology.Cells(cells)
		if len(cells) > 0:
			return topologic.Cell.Type()
		shells = cppyy.gbl.std.list[topologic.Shell.Ptr]()
		_ = topology.Shells(shells)
		if len(shells) > 0:
			return topologic.Shell.Type()
		faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = topology.Faces(faces)
		if len(faces) > 0:
			return topologic.Face.Type()
		wires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
		_ = topology.Wires(wires)
		if len(wires) > 0:
			return topologic.Wire.Type()
		edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		_ = topology.Edges(edges)
		if len(edges) > 0:
			return topologic.Edge.Type()
		vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = topology.Vertices(vertices)
		if len(vertices) > 0:
			return topologic.Vertex.Type()
	else:
		return(topology.GetType())

def processItem(item, operation):
	topologyA = item[0]
	topologyB = item[1]
	tranDict = item[2]
	tolerance = item[3]
	topologyC = None
	try:
		if operation == "Union":
			topologyC = fixTopologyClass(topologyA.Union(topologyB, False))
		elif operation == "Difference":
			topologyC = fixTopologyClass(topologyA.Difference(topologyB, False))
		elif operation == "Intersect":
			topologyC = fixTopologyClass(topologyA.Intersect(topologyB, False))
		elif operation == "SymDif":
			topologyC = fixTopologyClass(topologyA.XOR(topologyB, False))
		elif operation == "Merge":
			topologyC = fixTopologyClass(topologyA.Merge(topologyB)) # DEBUGGING
		elif operation == "Slice":
			topologyC = fixTopologyClass(topologyA.Slice(topologyB, False))
		elif operation == "Impose":
			topologyC = fixTopologyClass(topologyA.Impose(topologyB, False))
		elif operation == "Imprint":
			topologyC = fixTopologyClass(topologyA.Imprint(topologyB, False))
	except:
		print("ERROR: (Topologic>Topology.Boolean) operation failed.")
		topologyC = None
	if tranDict == True:
		print("Transfer Dictionary is True")
		sourceVertices = []
		sourceEdges = []
		sourceFaces = []
		sourceCells = []
		hidimA = highestDimension(topologyA)
		hidimB = highestDimension(topologyB)
		hidimC = highestDimension(topologyC)
		verticesA = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		if topologyA.Type() == topologic.Vertex.Type():
			verticesA.push_back(topologyA)
		elif hidimA >= topologic.Vertex.Type():
			_ = topologyA.Vertices(verticesA)
			for aVertex in verticesA:
				sourceVertices.append(aVertex)
		verticesB = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		if topologyB.Type() == topologic.Vertex.Type():
			verticesB.push_back(topologyB)
		elif hidimB >= topologic.Vertex.Type():
			_ = topologyB.Vertices(verticesB)
			for aVertex in verticesB:
				sourceVertices.append(aVertex)
		sinkVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		if topologyC.Type() == topologic.Vertex.Type():
			sinkVertices.push_back(topologyC)
		elif hidimC >= topologic.Vertex.Type():
			_ = topologyC.Vertices(sinkVertices)
		#_ = transferVertexDictionaries(sourceVertices, sinkVertices, tolerance)
		_ = transferDictionaries(sourceVertices, sinkVertices, tolerance)
		print("Boolean: Transfer Vertex Dictionaries Done")
		if topologyA.Type() == topologic.Edge.Type():
			sourceEdges.append(topologyA)
		elif hidimA >= topologic.Edge.Type():
			edgesA = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = topologyA.Edges(edgesA)
			for anEdge in edgesA:
				sourceEdges.append(anEdge)
		if topologyB.Type() == topologic.Edge.Type():
			sourceEdges.append(topologyB)
		elif hidimB >= topologic.Edge.Type():
			edgesB = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = topologyB.Edges(edgesB)
			for anEdge in edgesB:
				sourceEdges.append(anEdge)
		sinkEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		if topologyC.Type() == topologic.Edge.Type():
			sinkEdges.push_back(topologyC)
		elif hidimC >= topologic.Edge.Type():
			_ = topologyC.Edges(sinkEdges)
		print(sinkEdges)
		print("Boolean: Calling Transfer Edge Dictionaries")
		#_ = transferEdgeDictionaries(sourceEdges, sinkEdges, tolerance)
		_ = transferDictionaries(sourceEdges, sinkEdges, tolerance)
		print("Boolean: Transfer Edge Dictionaries Done")

		if topologyA.Type() == topologic.Face.Type():
			sourceFaces.append(topologyA)
		elif hidimA >= topologic.Face.Type():
			facesA = cppyy.gbl.std.list[topologic.Face.Ptr]()
			_ = topologyA.Faces(facesA)
			for aFace in facesA:
				sourceFaces.append(aFace)
		if topologyB.Type() == topologic.Face.Type():
			sourceFaces.append(topologyB)
		elif hidimB >= topologic.Face.Type():
			facesB = cppyy.gbl.std.list[topologic.Face.Ptr]()
			_ = topologyB.Faces(facesB)
			for aFace in facesB:
				sourceFaces.append(aFace)
		sinkFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		if topologyC.Type() == topologic.Face.Type():
			sinkFaces.push_back(topologyC)
		elif hidimC >= topologic.Face.Type():
			_ = topologyC.Faces(sinkFaces)
		print("Boolean: Calling Transfer Face Dictionaries")
		#_ = transferFaceDictionaries(sourceFaces, sinkFaces, tolerance)
		_ = transferDictionaries(sourceFaces, sinkFaces, tolerance)
		print("Boolean: Transfer Face Dictionaries Done")
		if topologyA.Type() == topologic.Cell.Type():
			sourceCells.append(topologyA)
		elif hidimA >= topologic.Cell.Type():
			cellsA = cppyy.gbl.std.list[topologic.Cell.Ptr]()
			_ = topologyA.Cells(cellsA)
			for aCell in cellsA:
				sourceCells.append(aCell)
		if topologyB.Type() == topologic.Cell.Type():
			sourceCells.append(topologyB)
		elif hidimB >= topologic.Cell.Type():
			cellsB = cppyy.gbl.std.list[topologic.Cell.Ptr]()
			_ = topologyB.Cells(cellsB)
			for aCell in cellsB:
				sourceCells.append(aCell)
		sinkCells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		if topologyC.Type() == topologic.Cell.Type():
			sinkCells.push_back(topologyC)
		elif hidimC >= topologic.Cell.Type():
			_ = topologyC.Cells(sinkCells)
		print("Boolean: Calling Transfer Cell Dictionaries")
		#_ = transferCellDictionaries(sourceCells, sinkCells, tolerance)
		_ = transferDictionaries(sourceCells, sinkCells, tolerance)
		print("Boolean: Transfer Cell Dictionaries Done")
	else:
		print("Transfer Dictionary is False")
	return topologyC

booleanOps = [("Union", "Union", "", 1),("Difference", "Difference", "", 2),("Intersect", "Intersect", "", 3),("SymDif", "SymDif", "", 4),("Merge", "Merge", "", 5), ("Slice", "Slice", "", 6),("Impose", "Impose", "", 7), ("Imprint", "Imprint", "", 8)]

class SvTopologyBoolean(bpy.types.Node, SverchCustomTreeNode):

	"""
	Triggers: Topologic
	Tooltip: Creates a Topology representing the Boolean operation of the two input Topologies
	"""
	bl_idname = 'SvTopologyBoolean'
	bl_label = 'Topology.Boolean'
	TransferDictionary: BoolProperty(name="Transfer Dictionary", default=False, update=updateNode)
	booleanOp: EnumProperty(name="Boolean Operation", description="Specify Boolean operation", default="Merge", items=booleanOps, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology A')
		self.inputs.new('SvStringsSocket', 'Topology B')
		self.inputs.new('SvStringsSocket', 'Transfer Dictionary').prop_name = 'TransferDictionary'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Topology')

	def draw_buttons(self, context, layout):
		layout.prop(self, "booleanOp",text="")

	def process(self):
		print(self.booleanOp)
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		topologyAList = self.inputs['Topology A'].sv_get(deepcopy=False)
		topologyBList = self.inputs['Topology B'].sv_get(deepcopy=False)
		tranDictList = self.inputs['Transfer Dictionary'].sv_get(deepcopy=False)[0]
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=False)[0]
		maxLength = max([len(topologyAList), len(topologyBList), len(tranDictList), len(toleranceList)])
		for i in range(len(topologyAList), maxLength):
			topologyAList.append(topologyAList[-1])
		for i in range(len(topologyBList), maxLength):
			topologyBList.append(topologyBList[-1])
		for i in range(len(tranDictList), maxLength):
			tranDictList.append(tranDictList[-1])
		for i in range(len(toleranceList), maxLength):
			toleranceList.append(toleranceList[-1])
		inputs = []
		outputs = []
		if (len(topologyAList) == len(topologyBList) == len(tranDictList) == len(toleranceList)):
			inputs = zip(topologyAList, topologyBList, tranDictList, toleranceList)
		for anInput in inputs:
			outputs.append(processItem(anInput, self.booleanOp))
		self.outputs['Topology'].sv_set(outputs)
		end = time.time()
		print(self.booleanOp+" Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyBoolean)

def unregister():
    bpy.utils.unregister_class(SvTopologyBoolean)
