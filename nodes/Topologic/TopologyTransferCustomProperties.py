import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import idprop

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
		return topology.CenterOfMass()

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

def getDictionary(source):
	keys = source.keys()
	print(keys)
	values = []
	for aKey in keys:
		value = source[aKey]
		values.append(source[aKey])
	print("Returning from getDictionary")
	return processKeysValues(keys, values)

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

def transferCustomProperties(sources, sinks, tol):
	for sink in sinks:
		sinkKeys = []
		sinkValues = []
		for source in sources:
			iv = topologic.Vertex.ByCoordinates(source.location.x, source.location.y, source.location.z)
			if topologyContains(sink, iv, tol):
				d = getDictionary(source)
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
						sourceValue = getValueAtKey(d, sourceKeys[i])
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
	if (topology.GetType() == topologic.Cluster.Type()):
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
	sinkVertices = []
	sinkEdges = []
	sinkFaces = []
	sinkCells = []
	hidimSink = highestDimension(sink)

	_ = transferCustomProperties(sources, [sink], tolerance)
	if tranVertices == True:
		sinkVertices = []
		if sink.Type() == topologic.Vertex.Type():
			sinkVertices.append(sink)
		elif hidimSink >= topologic.Vertex.Type():
			sink.Vertices(sinkVertices)
		_ = transferCustomProperties(sources, sinkVertices, tolerance)
	if tranEdges == True:
		sinkEdges = []
		if sink.Type() == topologic.Edge.Type():
			sinkEdges.append(sink)
		elif hidimSink >= topologic.Edge.Type():
			sink.Edges(sinkEdges)
		_ = transferCustomProperties(sources, sinkEdges, tolerance)
	if tranFaces == True:
		sinkFaces = []
		if sink.Type() == topologic.Face.Type():
			sinkFaces.append(sink)
		elif hidimSink >= topologic.Face.Type():
			sink.Faces(sinkFaces)
		_ = transferCustomProperties(sources, sinkFaces, tolerance)
	if tranCells == True:
		sinkCells = []
		if sink.Type() == topologic.Cell.Type():
			sinkCells.append(sink)
		elif hidimSink >= topologic.Cell.Type():
			sink.Cells(sinkCells)
		_ = transferCustomProperties(sources, sinkCells, tolerance)
	return sink

class SvTopologyTransferCustomProperties(bpy.types.Node, SverchCustomTreeNode):

	"""
	Triggers: Topologic
	Tooltip: Transfers the Custom Properties of the source Blender Geometries to the sink Topology based on specified options
	"""
	bl_idname = 'SvTopologyTransferCustomProperties'
	bl_label = 'Topology.TransferCustomProperties'
	TransferVertexProps: BoolProperty(name="Transfer Vertex Props", default=True, update=updateNode)
	TransferEdgeProps: BoolProperty(name="Transfer Edge Props", default=True, update=updateNode)
	TransferFaceProps: BoolProperty(name="Transfer Face Props", default=True, update=updateNode)
	TransferCellProps: BoolProperty(name="Transfer Cell Props", default=True, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Sources')
		self.inputs.new('SvStringsSocket', 'Sink')
		self.inputs.new('SvStringsSocket', 'Transfer Vertex Props').prop_name = 'TransferVertexProps'
		self.inputs.new('SvStringsSocket', 'Transfer Edge Props').prop_name = 'TransferEdgeProps'
		self.inputs.new('SvStringsSocket', 'Transfer Face Props').prop_name = 'TransferFaceProps'
		self.inputs.new('SvStringsSocket', 'Transfer Cell Props').prop_name = 'TransferCellProps'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Sink')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		sources = self.inputs['Sources'].sv_get(deepcopy=False)
		sink = self.inputs['Sink'].sv_get(deepcopy=False)[0]
		tranVertexProps = self.inputs['Transfer Vertex Props'].sv_get(deepcopy=False)[0][0]
		tranEdgeProps = self.inputs['Transfer Edge Props'].sv_get(deepcopy=False)[0][0]
		tranFaceProps = self.inputs['Transfer Face Props'].sv_get(deepcopy=False)[0][0]
		tranCellProps = self.inputs['Transfer Cell Props'].sv_get(deepcopy=False)[0][0]
		tolerance = self.inputs['Tolerance'].sv_get(deepcopy=False)[0][0]
		output = processItem(sources, sink, tranVertexProps, tranEdgeProps, tranFaceProps, tranCellProps, tolerance)
		self.outputs['Sink'].sv_set([output])
		end = time.time()
		print("Topology.TransferCustomProperties Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyTransferCustomProperties)

def unregister():
    bpy.utils.unregister_class(SvTopologyTransferCustomProperties)
