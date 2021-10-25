import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import time

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def repeat(list):
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

# From https://stackoverflow.com/questions/34432056/repeat-elements-of-list-between-each-other-until-we-reach-a-certain-length
def onestep(cur,y,base):
    # one step of the iteration
    if cur is not None:
        y.append(cur)
        base.append(cur)
    else:
        y.append(base[0])  # append is simplest, for now
        base = base[1:]+[base[0]]  # rotate
    return base

def iterate(list):
	maxLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		for i in range(len(anItem), maxLength):
			anItem.append(None)
		y=[]
		base=[]
		for cur in anItem:
			base = onestep(cur,y,base)
			# print(base,y)
		returnList.append(y)
	return returnList

def trim(list):
	minLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength < minLength:
			minLength = newLength
	for anItem in list:
		anItem = anItem[:minLength]
		returnList.append(anItem)
	return returnList

# Adapted from https://stackoverflow.com/questions/533905/get-the-cartesian-product-of-a-series-of-lists
def interlace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in interlace(ar_list[1:]):
                yield [a,]+prod

def transposeList(l):
	length = len(l[0])
	returnList = []
	for i in range(length):
		tempRow = []
		for j in range(len(l)):
			tempRow.append(l[j][i])
		returnList.append(tempRow)
	return returnList

def getValueAtKey(dict, key):
	returnValue = None
	try:
		returnValue = (cppyy.bind_object(dict.ValueAtKey(key).Value(), "std::string"))
	except:
		returnValue = None
	return returnValue

def relevantSelector(topology):
	returnVertex = None
	if topology.Type() == topologic.Vertex.Type():
		return topology
	elif topology.Type() == topologic.Edge.Type():
		return topologic.EdgeUtility.PointAtParameter(topology, 0.5)
	elif topology.Type() == topologic.Face.Type():
		return topologic.FaceUtility.InternalVertex(topology)
	elif topology.Type() == topologic.Cell.Type():
		return topologic.CellUtility.InternalVertex(topology)
	else:
		return topology.Centroid()

def topologyContains(topology, vertex, tol):
	contains = False
	if topology.Type() == topologic.Vertex.Type():
		try:
			contains = (topologic.VertexUtility.Distance(sourceVertex, vertex) <= tol)
		except:
			contains = False
		return contains
	elif topology.Type() == topologic.Edge.Type():
		try:
			_ = topologic.EdgeUtility.ParameterAtPoint(topology, vertex)
			contains = True
		except:
			contains = False
		return contains
	elif topology.Type() == topologic.Face.Type():
		return topologic.FaceUtility.IsInside(topology, vertex, tol)
	elif topology.Type() == topologic.Cell.Type():
		return (topologic.CellUtility.Contains(topology, vertex, tol) == 0)
	return False

def transferDictionaries(sources, sinks, tol):
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
		return(topology.Type())

def promote(item): #Fix Clusters with single entities
	resultingTopologies = []
	topCC = cppyy.gbl.std.list[topologic.CellComplex.Ptr]()
	_ = item.CellComplexes(topCC)
	topCC = list(topCC)
	topCells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
	_ = item.Cells(topCells)
	topCells = list(topCells)
	topShells = cppyy.gbl.std.list[topologic.Shell.Ptr]()
	_ = item.Shells(topShells)
	topShells = list(topShells)
	topFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	_ = item.Faces(topFaces)
	topFaces = list(topFaces)
	topWires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	_ = item.Wires(topWires)
	topWires = list(topWires)
	topEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	_ = item.Edges(topEdges)
	topEdges = list(topEdges)
	topVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	_ = item.Vertices(topVertices)
	topVertices = list(topVertices)
	if len(topCC) == 1:
		cc = topCC[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = cc.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(cc)
	if len(topCC) == 0 and len(topCells) == 1:
		cell = topCells[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = cell.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(cell)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 1:
		shell = topShells[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = shell.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(shell)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 1:
		face = topFaces[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = face.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(face)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 1:
		wire = topWires[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = wire.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(wire)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 0 and len(topEdges) == 1:
		edge = topEdges[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = wire.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(edge)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 0 and len(topEdges) == 0 and len(topVertices) == 1:
		vertex = topVertices[0]
		resultingTopologies.append(vertex)
	if len(resultingTopologies) == 1:
		return resultingTopologies[0]
	return item

def processItem(item):
	topologyA = item[0]
	topologyB = item[1]
	operation = item[2]
	tranDict = item[3]
	tolerance = item[4]
	topologyC = None
	try:
		if operation == "Union":
			topologyC = topologyA.Union(topologyB, False)
		elif operation == "Difference":
			topologyC = topologyA.Difference(topologyB, False)
		elif operation == "Intersect":
			topologyC = topologyA.Intersect(topologyB, False)
		elif operation == "SymDif":
			topologyC = topologyA.XOR(topologyB, False)
		elif operation == "Merge":
			topologyC = topologyA.Merge(topologyB, False)
		elif operation == "Slice":
			topologyC = topologyA.Slice(topologyB, False)
		elif operation == "Impose":
			topologyC = topologyA.Impose(topologyB, False)
		elif operation == "Imprint":
			topologyC = topologyA.Imprint(topologyB, False)
		else:
			raise Exception("ERROR: (Topologic>Topology.Boolean) invalid boolean operation name: "+operation)
	except:
		raise Exception("ERROR: (Topologic>Topology.Boolean) operation failed.")
		topologyC = None
	#topologyC = promote(topologyC)
	if tranDict == True:
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
		_ = transferDictionaries(sourceVertices, sinkVertices, tolerance)
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
		_ = transferDictionaries(sourceEdges, sinkEdges, tolerance)

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
		_ = transferDictionaries(sourceFaces, sinkFaces, tolerance)
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
		_ = transferDictionaries(sourceCells, sinkCells, tolerance)
	return topologyC

booleanOps = [("Union", "Union", "", 1),("Difference", "Difference", "", 2),("Intersect", "Intersect", "", 3),("SymDif", "SymDif", "", 4),("Merge", "Merge", "", 5), ("Slice", "Slice", "", 6),("Impose", "Impose", "", 7), ("Imprint", "Imprint", "", 8)]
replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvTopologyBoolean(bpy.types.Node, SverchCustomTreeNode):

	"""
	Triggers: Topologic
	Tooltip: Creates a Topology representing the Boolean operation of the two input Topologies
	"""
	bl_idname = 'SvTopologyBoolean'
	bl_label = 'Topology.Boolean'
	TransferDictionary: BoolProperty(name="Transfer Dictionary", default=False, update=updateNode)
	BooleanOp: EnumProperty(name="Boolean Operation", description="Specify Boolean operation", default="Merge", items=booleanOps, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology A')
		self.inputs.new('SvStringsSocket', 'Topology B')
		self.inputs.new('SvStringsSocket', 'Boolean Operation').prop_name = 'BooleanOp'
		self.inputs.new('SvStringsSocket', 'Transfer Dictionary').prop_name = 'TransferDictionary'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Topology')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		topologyAList = self.inputs['Topology A'].sv_get(deepcopy=True)
		topologyBList = self.inputs['Topology B'].sv_get(deepcopy=True)
		booleanOpList = self.inputs['Boolean Operation'].sv_get(deepcopy=True)
		tranDictList = self.inputs['Transfer Dictionary'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		topologyAList = flatten(topologyAList)
		topologyBList = flatten(topologyBList)
		booleanOpList = flatten(booleanOpList)
		tranDictList = flatten(tranDictList)
		toleranceList = flatten(toleranceList)
		inputs = [topologyAList, topologyBList, booleanOpList, tranDictList, toleranceList]
		if ((self.Replication) == "Trim"):
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
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)
		end = time.time()
		print("Topology.Boolean Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyBoolean)

def unregister():
    bpy.utils.unregister_class(SvTopologyBoolean)
