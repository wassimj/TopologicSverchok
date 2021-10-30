import bpy
from bpy.props import StringProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary

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

def getValueAtKey(dict, key):
	returnValue = None
	try:
		returnValue = str((cppyy.bind_object(dict.ValueAtKey(key).Value(), "std::string")))
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
		try:
			contains = (topologic.VertexUtility.Distance(topology, vertex) <= tol)
		except:
			contains = False
		return contains
	elif topology.GetType() == topologic.Edge.Type():
		try:
			_ = topologic.EdgeUtility.ParameterAtPoint(topology, vertex)
			contains = True
		except:
			contains = False
		return contains
	elif topology.GetType() == topologic.Face.Type():
		return topologic.FaceUtility.IsInside(topology, vertex, tol)
	elif topology.GetType() == topologic.Cell.Type():
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
				if d == None:
					continue
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

def processItem(sources, sink, tranVertices, tranEdges, tranFaces, tranCells, tolerance):
	sourceVertices = []
	sourceEdges = []
	sourceFaces = []
	sourceCells = []
	sinVertices = []
	sinkEdges = []
	sinkFaces = []
	sinkCells = []
	hidimSink = highestDimension(sink)
	if tranVertices == True:
		stlSinkVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		if sink.Type() == topologic.Vertex.Type():
			stlSinkVertices.push_back(sink)
		elif hidimSink >= topologic.Vertex.Type():
			sink.Vertices(stlSinkVertices)
			sinkVertices = list(stlSinkVertices)
	if tranEdges == True:
		stlSinkEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		if sink.Type() == topologic.Edge.Type():
			stlSinkEdges.push_back(sink)
		elif hidimSink >= topologic.Edge.Type():
			sink.Edges(stlSinkEdges)
			sinkEdges = list(stlSinkEdges)
	if tranFaces == True:
		stlSinkFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		if sink.Type() == topologic.Face.Type():
			stlSinkFaces.push_back(sink)
		elif hidimSink >= topologic.Face.Type():
			sink.Faces(stlSinkFaces)
			sinkFaces = list(stlSinkFaces)
	if tranCells == True:
		stlSinkCells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		if sink.Type() == topologic.Cell.Type():
			stlSinkCells.push_back(sink)
		elif hidimSink >= topologic.Cell.Type():
			sink.Cells(stlSinkCells)
			sinkCells = list(stlSinkCells)
	for source in sources:
		_ = transferDictionaries([source], [sink], tolerance)
		hidimSource = highestDimension(source)
		if tranVertices == True:
			stlSourceVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			if source.Type() == topologic.Vertex.Type():
				stlSourceVertices.push_back(source)
			elif hidimSource >= topologic.Vertex.Type():
				source.Vertices(stlSourceVertices)
				sourceVertices = list(stlSourceVertices)
			_ = transferDictionaries(sourceVertices, sinkVertices, tolerance)
		if tranEdges == True:
			if source.Type() == topologic.Edge.Type():
				sourceEdges.append(source)
			elif hidimSource >= topologic.Edge.Type():
				stlSourceEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
				source.Edges(stlSourceEdges)
				sourceEdges = list(stlSourceEdges)
			_ = transferDictionaries(sourceEdges, sinkEdges, tolerance)
		if tranFaces == True:
			if source.Type() == topologic.Face.Type():
				sourceFaces.append(source)
			elif hidimSource >= topologic.Face.Type():
				stlSourceFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
				source.Faces(stlSourceFaces)
				sourceFaces = list(stlSourceFaces)
			_ = transferDictionaries(sourceFaces, sinkFaces, tolerance)
		if tranCells == True:
			if source.Type() == topologic.Cell.Type():
				sourceCells.append(source)
			elif hidimSource >= topologic.Cell.Type():
				stlSourceCells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
				source.Cells(stlSourceCells)
				sourceCells = list(stlSourceCells)
			_ = transferDictionaries(sourceCells, sinkCells, tolerance)
	return sink

class SvTopologySetDictionaries(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Sets the input dictionaries for the sub-topologies of the input Topology using the input selector Vertices
	"""
	bl_idname = 'SvTopologySetDictionaries'
	bl_label = 'Topology.SetDictionaries'
	TypeFilter: IntProperty(name="Type Filter", default=255, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Selectors')
		self.inputs.new('SvStringsSocket', 'Dictionaries')
		self.inputs.new('SvStringsSocket', 'Type Filter').prop_name = 'TypeFilter'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topology = self.inputs['Topology'].sv_get(deepcopy=False)[0] #Consider only one Topology
		selectorList = flatten(self.inputs['Selectors'].sv_get(deepcopy=False))
		dictionaryList = flatten(self.inputs['Dictionaries'].sv_get(deepcopy=False))
		typeFilter = self.inputs['Type Filter'].sv_get(deepcopy=False)[0][0] #Consider only one TypeFilter
		if len(selectorList) != len(dictionaryList):
			return
		selectors = convert_to_stl_list(selectorList, Vertex.Ptr)
		dictionaries = convert_to_stl_list(dictionaryList, Dictionary)
		for aDictionary in dictionaries:
			values = aDictionary.Values()
			returnList = []
			for aValue in values:
				s = cppyy.bind_object(aValue.Value(), 'StringStruct')
				returnList.append(str(s.getString))
			print(returnList)
		result = topology.SetDictionaries(selectors, dictionaries, typeFilter)
		result = fixTopologyClass(result)
		self.outputs['Topology'].sv_set([result])

def register():
	bpy.utils.register_class(SvTopologySetDictionaries)

def unregister():
	bpy.utils.unregister_class(SvTopologySetDictionaries)
