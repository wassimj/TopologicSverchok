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

def listAttributeValues(listAttribute):
	listAttributes = listAttribute.ListValue()
	returnList = []
	for attr in listAttributes:
		if isinstance(attr, IntAttribute):
			returnList.append(attr.IntValue())
		elif isinstance(attr, DoubleAttribute):
			returnList.append(attr.DoubleValue())
		elif isinstance(attr, StringAttribute):
			returnList.append(attr.StringValue())
	return returnList

def getValueAtKey(item, key):
	try:
		attr = item.ValueAtKey(key)
	except:
		raise Exception("Dictionary.ValueAtKey - Error: Could not retrieve a Value at the specified key ("+key+")")
	if isinstance(attr, topologic.IntAttribute):
		return (attr.IntValue())
	elif isinstance(attr, topologic.DoubleAttribute):
		return (attr.DoubleValue())
	elif isinstance(attr, topologic.StringAttribute):
		return (attr.StringValue())
	elif isinstance(attr, topologic.ListAttribute):
		return (listAttributeValues(attr))
	else:
		return None

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

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("DictionaryByKeysValues - Keys and Values do not have the same length")
	stl_keys = []
	stl_values = []
	for i in range(len(keys)):
		if isinstance(keys[i], str):
			stl_keys.append(keys[i])
		else:
			stl_keys.append(str(keys[i]))
		if isinstance(values[i], list) and len(values[i]) == 1:
			value = values[i][0]
		else:
			value = values[i]
		if isinstance(value, bool):
			if value == False:
				stl_values.append(topologic.IntAttribute(0))
			else:
				stl_values.append(topologic.IntAttribute(1))
		elif isinstance(value, int):
			stl_values.append(topologic.IntAttribute(value))
		elif isinstance(value, float):
			stl_values.append(topologic.DoubleAttribute(value))
		elif isinstance(value, str):
			stl_values.append(topologic.StringAttribute(value))
		elif isinstance(value, list):
			l = []
			for v in value:
				if isinstance(v, bool):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, int):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, float):
					l.append(topologic.DoubleAttribute(v))
				elif isinstance(v, str):
					l.append(topologic.StringAttribute(v))
			stl_values.append(topologic.ListAttribute(l))
		else:
			raise Exception("Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
	myDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
	return myDict

def transferDictionaries(sources, sinks, tol):
	for sink in sinks:
		sinkKeys = []
		sinkValues = []
		iv = relevantSelector(sink)
		j = 1
		for source in sources:
			if topologyContains(source, iv, tol):
				d = source.GetDictionary()
				if d == None:
					continue
				stlKeys = d.Keys()
				if len(stlKeys) > 0:
					sourceKeys = d.Keys()
					for aSourceKey in sourceKeys:
						if aSourceKey not in sinkKeys:
							sinkKeys.append(aSourceKey)
							sinkValues.append("")
					for i in range(len(sourceKeys)):
						index = sinkKeys.index(sourceKeys[i])
						sourceValue = valueAtKey(d, sourceKeys[i])
						if sourceValue != None:
							if sinkValues[index] != "":
								if isinstance(sinkValues[index], list):
									sinkValues[index].append(sourceValue)
								else:
									sinkValues[index] = [sinkValues[index], sourceValue]
							else:
								sinkValues[index] = sourceValue
		if len(sinkKeys) > 0 and len(sinkValues) > 0:
			newDict = processKeysValues(sinkKeys, sinkValues)
			_ = sink.SetDictionary(newDict)

def highestDimension(topology):
	if (topology.Type() == topologic.Cluster.Type()):
		cellComplexes = []
		_ = topology.CellComplexes(None, cellComplexes)
		if len(cellComplexes) > 0:
			return topologic.CellComplex.Type()
		cells = []
		_ = topology.Cells(None, cells)
		if len(cells) > 0:
			return topologic.Cell.Type()
		shells = []
		_ = topology.Shells(None, shells)
		if len(shells) > 0:
			return topologic.Shell.Type()
		faces = []
		_ = topology.Faces(None, faces)
		if len(faces) > 0:
			return topologic.Face.Type()
		wires = []
		_ = topology.Wires(None, wires)
		if len(wires) > 0:
			return topologic.Wire.Type()
		edges = []
		_ = topology.Edges(None, edges)
		if len(edges) > 0:
			return topologic.Edge.Type()
		vertices = []
		_ = topology.Vertices(None, vertices)
		if len(vertices) > 0:
			return topologic.Vertex.Type()
	else:
		return(topology.Type())

def promote(item): #Fix Clusters with single entities
	resultingTopologies = []
	topCC = []
	_ = item.CellComplexes(None, topCC)
	topCells = []
	_ = item.Cells(None, topCells)
	topShells = []
	_ = item.Shells(None, topShells)
	topFaces = []
	_ = item.Faces(None, topFaces)
	topWires = []
	_ = item.Wires(None, topWires)
	topEdges = []
	_ = item.Edges(None, topEdges)
	topVertices = []
	_ = item.Vertices(None, topVertices)
	if len(topCC) == 1:
		cc = topCC[0]
		ccVertices = []
		_ = cc.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(cc)
	if len(topCC) == 0 and len(topCells) == 1:
		cell = topCells[0]
		ccVertices = []
		_ = cell.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(cell)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 1:
		shell = topShells[0]
		ccVertices = []
		_ = shell.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(shell)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 1:
		face = topFaces[0]
		ccVertices = []
		_ = face.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(face)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 1:
		wire = topWires[0]
		ccVertices = []
		_ = wire.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(wire)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 0 and len(topEdges) == 1:
		edge = topEdges[0]
		ccVertices = []
		_ = wire.Vertices(None, ccVertices)
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
		verticesA = []
		if topologyA.Type() == topologic.Vertex.Type():
			verticesA.append(topologyA)
		elif hidimA >= topologic.Vertex.Type():
			_ = topologyA.Vertices(None, verticesA)
			for aVertex in verticesA:
				sourceVertices.append(aVertex)
		verticesB = []
		if topologyB.Type() == topologic.Vertex.Type():
			verticesB.append(topologyB)
		elif hidimB >= topologic.Vertex.Type():
			_ = topologyB.Vertices(None, verticesB)
			for aVertex in verticesB:
				sourceVertices.append(aVertex)
		sinkVertices = []
		if topologyC.Type() == topologic.Vertex.Type():
			sinkVertices.append(topologyC)
		elif hidimC >= topologic.Vertex.Type():
			_ = topologyC.Vertices(None, sinkVertices)
		_ = transferDictionaries(sourceVertices, sinkVertices, tolerance)
		if topologyA.Type() == topologic.Edge.Type():
			sourceEdges.append(topologyA)
		elif hidimA >= topologic.Edge.Type():
			edgesA = []
			_ = topologyA.Edges(None, edgesA)
			for anEdge in edgesA:
				sourceEdges.append(anEdge)
		if topologyB.Type() == topologic.Edge.Type():
			sourceEdges.append(topologyB)
		elif hidimB >= topologic.Edge.Type():
			edgesB = []
			_ = topologyB.Edges(None, edgesB)
			for anEdge in edgesB:
				sourceEdges.append(anEdge)
		sinkEdges = []
		if topologyC.Type() == topologic.Edge.Type():
			sinkEdges.append(topologyC)
		elif hidimC >= topologic.Edge.Type():
			_ = topologyC.Edges(None, sinkEdges)
		_ = transferDictionaries(sourceEdges, sinkEdges, tolerance)

		if topologyA.Type() == topologic.Face.Type():
			sourceFaces.append(topologyA)
		elif hidimA >= topologic.Face.Type():
			facesA = []
			_ = topologyA.Faces(facesA)
			for aFace in facesA:
				sourceFaces.append(aFace)
		if topologyB.Type() == topologic.Face.Type():
			sourceFaces.append(topologyB)
		elif hidimB >= topologic.Face.Type():
			facesB = []
			_ = topologyB.Faces(facesB)
			for aFace in facesB:
				sourceFaces.append(aFace)
		sinkFaces = []
		if topologyC.Type() == topologic.Face.Type():
			sinkFaces.append(topologyC)
		elif hidimC >= topologic.Face.Type():
			_ = topologyC.Faces(sinkFaces)
		_ = transferDictionaries(sourceFaces, sinkFaces, tolerance)
		if topologyA.Type() == topologic.Cell.Type():
			sourceCells.append(topologyA)
		elif hidimA >= topologic.Cell.Type():
			cellsA = []
			_ = topologyA.Cells(None, cellsA)
			for aCell in cellsA:
				sourceCells.append(aCell)
		if topologyB.Type() == topologic.Cell.Type():
			sourceCells.append(topologyB)
		elif hidimB >= topologic.Cell.Type():
			cellsB = []
			_ = topologyB.Cells(None, cellsB)
			for aCell in cellsB:
				sourceCells.append(aCell)
		sinkCells = []
		if topologyC.Type() == topologic.Cell.Type():
			sinkCells.append(topologyC)
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
