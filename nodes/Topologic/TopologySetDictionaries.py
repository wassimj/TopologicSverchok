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

def relevantSelector(topology, tol):
	returnVertex = None
	if topology.Type() == topologic.Vertex.Type():
		return topology
	elif topology.Type() == topologic.Edge.Type():
		return topologic.EdgeUtility.PointAtParameter(topology, 0.5)
	elif topology.Type() == topologic.Face.Type():
		return topologic.FaceUtility.InternalVertex(topology)
	elif topology.Type() == topologic.Cell.Type():
		return topologic.CellUtility.InternalVertex(topology, tol)
	else:
		return topology.Centroid()

def topologyContains(topology, vertex, tol):
	contains = False
	if topology.Type() == topologic.Vertex.Type():
		try:
			contains = (topologic.VertexUtility.Distance(topology, vertex) <= tol)
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
		iv = relevantSelector(sink, tol)
		j = 1
		for source in sources:
			if topologyContains(source, iv, tol):
				d = source.GetDictionary()
				if d == None:
					continue
				sourceKeys= d.Keys()
				if len(sourceKeys) > 0:
					for aSourceKey in sourceKeys:
						if aSourceKey not in sinkKeys:
							sinkKeys.append(aSourceKey)
							sinkValues.append("")
					for i in range(len(sourceKeys)):
						index = sinkKeys.index(sourceKeys[i])
						sourceValue = getValueAtKey(d, sourceKeys[i])
						if sourceValue != None:
							if sinkValues[index] != "":
								sinkValues[index].append(sourceValue)
							else:
								sinkValues[index] = sourceValue
		if len(sinkKeys) > 0 and len(sinkValues) > 0:
			newDict = processKeysValues(sinkKeys, sinkValues)
			_ = sink.SetDictionary(newDict)

def transferDictionariesUniversal(sources, sinks, tol):
	print("Entering transferDictionariesUniversal")
	for sink in sinks:
		sinkKeys = []
		sinkValues = []
		j = 1
		for source in sources:
			d = source.GetDictionary()
			if d == None:
				continue
			sourceKeys= d.Keys()
			if len(sourceKeys) > 0:
				for aSourceKey in sourceKeys:
					if aSourceKey not in sinkKeys:
						sinkKeys.append(aSourceKey)
						sinkValues.append("")
				for i in range(len(sourceKeys)):
					index = sinkKeys.index(sourceKeys[i])
					sourceValue = getValueAtKey(d, sourceKeys[i])
					if sourceValue != None:
						if sinkValues[index] != "":
							sinkValues[index].append(sourceValue)
						else:
							sinkValues[index] = sourceValue
		if len(sinkKeys) > 0 and len(sinkValues) > 0:
			print(sinkValues)
			newDict = processKeysValues(sinkKeys, sinkValues)
			_ = sink.SetDictionary(newDict)

def highestDimension(topology):
	if (topology.Type() == topologic.Cluster.Type()):
		cellComplexes = []
		_ = topology.CellComplexes(cellComplexes)
		if len(cellComplexes) > 0:
			return topologic.CellComplex.Type()
		cells = []
		_ = topology.Cells(cells)
		if len(cells) > 0:
			return topologic.Cell.Type()
		shells = []
		_ = topology.Shells(shells)
		if len(shells) > 0:
			return topologic.Shell.Type()
		faces = []
		_ = topology.Faces(faces)
		if len(faces) > 0:
			return topologic.Face.Type()
		wires = []
		_ = topology.Wires(wires)
		if len(wires) > 0:
			return topologic.Wire.Type()
		edges = []
		_ = topology.Edges(edges)
		if len(edges) > 0:
			return topologic.Edge.Type()
		vertices = []
		_ = topology.Vertices(vertices)
		if len(vertices) > 0:
			return topologic.Vertex.Type()
	else:
		return(topology.Type())

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
		if sink.Type() == topologic.Vertex.Type():
			sinkVertices.append(sink)
		elif hidimSink >= topologic.Vertex.Type():
			sink.Vertices(sinkVertices)
	if tranEdges == True:
		if sink.Type() == topologic.Edge.Type():
			sinkEdges.append(sink)
		elif hidimSink >= topologic.Edge.Type():
			sink.Edges(sinkEdges)
	if tranFaces == True:
		if sink.Type() == topologic.Face.Type():
			sinkFaces.append(sink)
		elif hidimSink >= topologic.Face.Type():
			sink.Faces(sinkFaces)
	if tranCells == True:
		if sink.Type() == topologic.Cell.Type():
			sinkCells.append(sink)
		elif hidimSink >= topologic.Cell.Type():
			sink.Cells(sinkCells)
	for source in sources:
		_ = transferDictionariesUniversal([source], [sink], tolerance)
		hidimSource = highestDimension(source)
		if tranVertices == True:
			if source.Type() == topologic.Vertex.Type():
				sourceVertices.append(source)
			elif hidimSource >= topologic.Vertex.Type():
				source.Vertices(sourceVertices)
			_ = transferDictionaries(sourceVertices, sinkVertices, tolerance)
		if tranEdges == True:
			if source.Type() == topologic.Edge.Type():
				sourceEdges.append(source)
			elif hidimSource >= topologic.Edge.Type():
				source.Edges(sourceEdges)
			_ = transferDictionaries(sourceEdges, sinkEdges, tolerance)
		if tranFaces == True:
			if source.Type() == topologic.Face.Type():
				sourceFaces.append(source)
			elif hidimSource >= topologic.Face.Type():
				source.Faces(sourceFaces)
			_ = transferDictionaries(sourceFaces, sinkFaces, tolerance)
		if tranCells == True:
			if source.Type() == topologic.Cell.Type():
				sourceCells.append(source)
			elif hidimSource >= topologic.Cell.Type():
				source.Cells(sourceCells)
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
