import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import json
import os

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def relevantSelector(topology, tol):
	returnVertex = None
	if topology.Type() == topologic.Vertex.Type():
		return topology
	elif topology.Type() == topologic.Edge.Type():
		return topologic.EdgeUtility.PointAtParameter(topology, 0.5)
	elif topology.Type() == topologic.Face.Type():
		return topologic.FaceUtility.InternalVertex(topology, tol)
	elif topology.Type() == topologic.Cell.Type():
		return topologic.CellUtility.InternalVertex(topology, tol)
	else:
		return topology.CenterOfMass()

def topologyContains(topology, vertex, tol):
	contains = False
	if topology.Type() == topologic.Vertex.Type():
		try:
			contains = (topologic.VertexUtility.Distance(vertex, topology) <= tol)
		except:
			contains = False
		return contains
	elif topology.Type() == topologic.Edge.Type():
		try:
			contains = (topologic.VertexUtility.Distance(vertex, topology) <= tol)
		except:
			contains = False
		return contains
	elif topology.Type() == topologic.Face.Type():
		return topologic.FaceUtility.IsInside(topology, vertex, tol)
	elif topology.Type() == topologic.Cell.Type():
		return (topologic.CellUtility.Contains(topology, vertex, tol) == 0)
	return False

def listAttributeValues(listAttribute):
	listAttributes = listAttribute.ListValue()
	returnList = []
	for attr in listAttributes:
		if isinstance(attr, topologic.IntAttribute):
			returnList.append(attr.IntValue())
		elif isinstance(attr, topologic.DoubleAttribute):
			returnList.append(attr.DoubleValue())
		elif isinstance(attr, topologic.StringAttribute):
			returnList.append(attr.StringValue())
	return returnList

def valueAtKey(item, key):
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

def transferDictionaries(sources, sinks, tol):
	usedSources = []
	for i in range(len(sources)):
		usedSources.append(False)
	for sink in sinks:
		sinkKeys = []
		sinkValues = []
		for j in range(len(sources)):
			source = sources[j]
			if usedSources[j] == False:
				d = source.GetDictionary()
				if d:
					sourceKeys = d.Keys()
					if len(sourceKeys) > 0:
						iv = relevantSelector(source, tol)
						if topologyContains(sink, iv, tol):
							usedSources[j] = True
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
					else:
						usedSources[j] = True # Has no keys so not useful to reconsider
				else:
					usedSources[j] = True # Has no dictionary so not useful to reconsider
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

def processSelectors(sources, sink, tranVertices, tranEdges, tranFaces, tranCells, tolerance):
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
		sinkVertices = []
		if sink.Type() == topologic.Vertex.Type():
			sinkVertices.append(sink)
		elif hidimSink >= topologic.Vertex.Type():
			sink.Vertices(None, sinkVertices)
		_ = transferDictionaries(sources, sinkVertices, tolerance)
	if tranEdges == True:
		sinkEdges = []
		if sink.Type() == topologic.Edge.Type():
			sinkEdges.append(sink)
		elif hidimSink >= topologic.Edge.Type():
			sink.Edges(None, sinkEdges)
			_ = transferDictionaries(sources, sinkEdges, tolerance)
	if tranFaces == True:
		sinkFaces = []
		if sink.Type() == topologic.Face.Type():
			sinkFaces.append(sink)
		elif hidimSink >= topologic.Face.Type():
			sink.Faces(None, sinkFaces)
		_ = transferDictionaries(sources, sinkFaces, tolerance)
	if tranCells == True:
		sinkCells = []
		if sink.Type() == topologic.Cell.Type():
			sinkCells.append(sink)
		elif hidimSink >= topologic.Cell.Type():
			sink.Cells(None, sinkCells)
		_ = transferDictionaries(sources, sinkCells, tolerance)
	return sink

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

def isInside(aperture, face, tolerance):
	return (topologic.VertexUtility.Distance(aperture.Topology.Centroid(), face) < tolerance)

def internalVertex(topology, tolerance):
	vst = None
	classType = topology.Type()
	if classType == 64: #CellComplex
		tempCells = []
		_ = topology.Cells(tempCells)
		tempCell = tempCells[0]
		vst = topologic.CellUtility.InternalVertex(tempCell, tolerance)
	elif classType == 32: #Cell
		vst = topologic.CellUtility.InternalVertex(topology, tolerance)
	elif classType == 16: #Shell
		tempFaces = []
		_ = topology.Faces(None, tempFaces)
		tempFace = tempFaces[0]
		vst = topologic.FaceUtility.InternalVertex(tempFace, tolerance)
	elif classType == 8: #Face
		vst = topologic.FaceUtility.InternalVertex(topology, tolerance)
	elif classType == 4: #Wire
		if topology.IsClosed():
			internalBoundaries = []
			tempFace = topologic.Face.ByExternalInternalBoundaries(topology, internalBoundaries)
			vst = topologic.FaceUtility.InternalVertex(tempFace, tolerance)
		else:
			tempEdges = []
			_ = topology.Edges(None, tempEdges)
			vst = topologic.EdgeUtility.PointAtParameter(tempVertex[0], 0.5)
	elif classType == 2: #Edge
		vst = topologic.EdgeUtility.PointAtParameter(topology, 0.5)
	elif classType == 1: #Vertex
		vst = topology
	else:
		vst = topology.Centroid()
	return vst

def processApertures(subTopologies, apertures, exclusive, tolerance):
	usedTopologies = []
	for subTopology in subTopologies:
			usedTopologies.append(0)
	ap = 1
	for aperture in apertures:
		apCenter = internalVertex(aperture, tolerance)
		for i in range(len(subTopologies)):
			subTopology = subTopologies[i]
			if exclusive == True and usedTopologies[i] == 1:
				continue
			if topologic.VertexUtility.Distance(apCenter, subTopology) < tolerance:
				context = topologic.Context.ByTopologyParameters(subTopology, 0.5, 0.5, 0.5)
				_ = topologic.Aperture.ByTopologyContext(aperture, context)
				if exclusive == True:
					usedTopologies[i] = 1
		ap = ap + 1
	return None

def getApertures(apertureList, folderPath):
	returnApertures = []
	for item in apertureList:
		brepFileName = item['brep']
		brepFilePath = os.path.join(folderPath, brepFileName+".brep")
		print(brepFilePath)
		brepFile = open(brepFilePath)
		if brepFile:
			brepString = brepFile.read()
			aperture = topologic.Topology.ByString(brepString)
			brepFile.close()
		dictionary = item['dictionary']
		keys = list(dictionary.keys())
		values = []
		for key in keys:
			values.append(dictionary[key])
		topDictionary = processKeysValues(keys, values)
		if len(keys) > 0:
			_ = aperture.SetDictionary(topDictionary)
		returnApertures.append(aperture)
	return returnApertures

def dictionaryByPythonDictionary(pydict):
	keys = list(pydict.keys())
	values = []
	for key in keys:
		values.append(pydict[key])
	return processKeysValues(keys, values)

def assignDictionary(item):
	selector = item['selector']
	pydict = item['dictionary']
	v = topologic.Vertex.ByCoordinates(selector[0], selector[1], selector[2])
	d = dictionaryByPythonDictionary(pydict)
	_ = v.SetDictionary(d)
	return v

def processItem(jsonFilePath):
	topology = None
	jsonFile = open(jsonFilePath)
	folderPath = os.path.dirname(jsonFilePath)
	if jsonFile:
		topologies = []
		jsondata = json.load(jsonFile)
		for jsonItem in jsondata:
			brepFileName = jsonItem['brep']
			brepFilePath = os.path.join(folderPath, brepFileName+".brep")
			brepFile = open(brepFilePath)
			if brepFile:
				brepString = brepFile.read()
				topology = topologic.Topology.ByString(brepString)
				brepFile.close()
			#topology = topologic.Topology.ByString(brep)
			dictionary = jsonItem['dictionary']
			topDictionary = dictionaryByPythonDictionary(dictionary)
			_ = topology.SetDictionary(topDictionary)
			cellApertures = getApertures(jsonItem['cellApertures'], folderPath)
			cells = []
			try:
				_ = topology.Cells(None, cells)
			except:
				pass
			processApertures(cells, cellApertures, False, 0.001)
			faceApertures = getApertures(jsonItem['faceApertures'], folderPath)
			faces = []
			try:
				_ = topology.Faces(None, faces)
			except:
				pass
			processApertures(faces, faceApertures, False, 0.001)
			edgeApertures = getApertures(jsonItem['edgeApertures'], folderPath)
			edges = []
			try:
				_ = topology.Edges(None, edges)
			except:
				pass
			processApertures(edges, edgeApertures, False, 0.001)
			vertexApertures = getApertures(jsonItem['vertexApertures'], folderPath)
			vertices = []
			try:
				_ = topology.Vertices(None, vertices)
			except:
				pass
			processApertures(vertices, vertexApertures, False, 0.001)
			cellDataList = jsonItem['cellDictionaries']
			cellSelectors = []
			for cellDataItem in cellDataList:
				cellSelectors.append(assignDictionary(cellDataItem))
			processSelectors(cellSelectors, topology, False, False, False, True, 0.001)
			faceDataList = jsonItem['faceDictionaries']
			faceSelectors = []
			for faceDataItem in faceDataList:
				faceSelectors.append(assignDictionary(faceDataItem))
			processSelectors(faceSelectors, topology, False, False, True, False, 0.001)
			edgeDataList = jsonItem['edgeDictionaries']
			edgeSelectors = []
			for edgeDataItem in edgeDataList:
				edgeSelectors.append(assignDictionary(edgeDataItem))
			processSelectors(edgeSelectors, topology, False, True, False, False, 0.001)
			vertexDataList = jsonItem['vertexDictionaries']
			vertexSelectors = []
			for vertexDataItem in vertexDataList:
				vertexSelectors.append(assignDictionary(vertexDataItem))
			processSelectors(vertexSelectors, topology, True, False, False, False, 0.001)
			topologies.append(topology)
		return topologies
	return None
		
class SvTopologyByImportedJSONMK2(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology from the input BREP file
	"""
	bl_idname = 'SvTopologyByImportedJSONMK2'
	bl_label = 'Topology.ByImportedJSON MK2'
	FilePath: StringProperty(name="File Path", default="", subtype="FILE_PATH")

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'File Path').prop_name='FilePath'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['File Path'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyByImportedJSONMK2)

def unregister():
	bpy.utils.unregister_class(SvTopologyByImportedJSONMK2)
