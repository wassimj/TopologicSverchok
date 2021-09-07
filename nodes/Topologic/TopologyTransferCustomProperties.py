import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import idprop

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import cppyy
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

def getKeys(item):
	stl_keys = item.Keys()
	returnList = []
	copyKeys = stl_keys.__class__(stl_keys) #wlav suggested workaround. Make a copy first
	for x in copyKeys:
		k = x.c_str()
		returnList.append(k)
	return returnList

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
		return topology.CenterOfMass()

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

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("Keys and Values do not have the same length")
	stl_keys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
	stl_values = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
	for i in range(len(keys)):
		if isinstance(values[i], list) and len(values[i]) == 1:
			value = values[i][0]
		else:
			value = values[i]
		print("VALUE IS: ",value)
		if isinstance(value, bool):
			stl_keys.push_back(keys[i])
			if value == False:
				stl_values.push_back(topologic.IntAttribute(0))
			else:
				stl_values.push_back(topologic.IntAttribute(1))
		elif isinstance(value, int):
			stl_keys.push_back(keys[i])
			stl_values.push_back(topologic.IntAttribute(value))
		elif isinstance(value, float):
			stl_keys.push_back(keys[i])
			stl_values.push_back(topologic.DoubleAttribute(value))
		elif isinstance(value, str):
			stl_keys.push_back(keys[i])
			stl_values.push_back(topologic.StringAttribute(value))
		elif isinstance(value, list):
			stl_keys.push_back(keys[i])
			l = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
			for v in value:
				if isinstance(v, bool):
					l.push_back(topologic.IntAttribute(v))
				elif isinstance(v, int):
					l.push_back(topologic.IntAttribute(v))
				elif isinstance(v, float):
					l.push_back(topologic.DoubleAttribute(v))
				elif isinstance(v, str):
					l.push_back(topologic.StringAttribute(v))
			stl_values.push_back(topologic.ListAttribute(l))
		elif isinstance(value, idprop.types.IDPropertyArray):
			value = value.to_list()
			print(value)
			stl_keys.push_back(keys[i])
			l = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
			for v in value:
				if isinstance(v, bool):
					l.push_back(topologic.IntAttribute(v))
				elif isinstance(v, int):
					l.push_back(topologic.IntAttribute(v))
				elif isinstance(v, float):
					l.push_back(topologic.DoubleAttribute(v))
				elif isinstance(v, str):
					l.push_back(topologic.StringAttribute(v))
			stl_values.push_back(topologic.ListAttribute(l))
			print("Done pushing values")
		else:
			#raise Exception("Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
			continue
	print("Almost Done. Returning")
	return topologic.Dictionary.ByKeysValues(stl_keys, stl_values)

def getDictionary(source):
	keys = source.keys()
	print(keys)
	values = []
	for aKey in keys:
		value = source[aKey]
		values.append(source[aKey])
	print("Returning from getDictionary")
	return processKeysValues(keys, values)

def transferCustomProperties(sources, sinks, tol):
	for sink in sinks:
		sinkKeys = []
		sinkValues = []
		for source in sources:
			iv = topologic.Vertex.ByCoordinates(source.location.x, source.location.y, source.location.z)
			print([iv.X(), iv.Y(), iv.Z()])
			if topologyContains(sink, iv, tol):
				print("Found Container!")
				d = getDictionary(source)
				print("Got the Dictionary")
				print(d)
				if d == None:
					continue
				stlKeys = d.Keys()
				if len(stlKeys) > 0:
					sourceKeys = getKeys(d)
					for aSourceKey in sourceKeys:
						if aSourceKey not in sinkKeys:
							sinkKeys.append(aSourceKey)
							sinkValues.append("")
					for i in range(len(sourceKeys)):
						index = sinkKeys.index(sourceKeys[i])
						k = cppyy.gbl.std.string(sourceKeys[i])
						sourceValue = d.ValueAtKey(k).Value()
						if sourceValue:
							if (isinstance(sourceValue, cppyy.gbl.std.string)):
								sourceValue = sourceValue.c_str()
							if sinkValues[index] != "":
								if isinstance(sinkValues[index], list):
									sinkValues[index].append(sourceValue)
								else:
									sinkValues[index] = [sinkValues[index], sourceValue]
							else:
								sinkValues[index] = sourceValue
		print("STEP 1")
		if len(sinkKeys) > 0 and len(sinkValues) > 0:
			stlKeys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
			for sinkKey in sinkKeys:
				stlKeys.push_back(sinkKey)
			stlValues = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
			print("STEP 2")
			for sinkValue in sinkValues:
				if isinstance(sinkValue, bool):
					print("IT IS A BOOLEAN!!!!")
					stlValues.push_back(topologic.IntAttribute(sinkValue))
				elif isinstance(sinkValue, int):
					print("IT IS AN INTEGER!!!!")
					stlValues.push_back(topologic.IntAttribute(sinkValue))
				elif isinstance(sinkValue, float):
					print("IT IS A FLOAT!!!!")
					stlValues.push_back(topologic.DoubleAttribute(sinkValue))
				elif isinstance(sinkValue, str):
					print("IT IS A STRING!!!!")
					stlValues.push_back(topologic.StringAttribute(sinkValue))
				elif isinstance(sinkValue, list) or isinstance(sinkValue, cppyy.gbl.std.list[topologic.Attribute.Ptr]):
					print("IT IS A LIST!!!!")
					l = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
					for v in sinkValue:
						print(v)
						if isinstance(v, bool):
							l.push_back(topologic.IntAttribute(v))
						elif isinstance(v, int):
							l.push_back(topologic.IntAttribute(v))
						elif isinstance(v, float):
							l.push_back(topologic.DoubleAttribute(v))
						elif isinstance(v, str):
							l.push_back(topologic.StringAttribute(v))
						else:
							l.push_back(v)
					stlValues.push_back(topologic.ListAttribute(l))
			print("Creating a NEW DICTIONARY")
			newDict = topologic.Dictionary.ByKeysValues(stlKeys, stlValues)
			print("Setting the dictionary to the SINK")
			_ = sink.SetDictionary(newDict)
			print("DONE WITH transferCustomProperties")

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
	sinkVertices = []
	sinkEdges = []
	sinkFaces = []
	sinkCells = []
	hidimSink = highestDimension(sink)

	_ = transferCustomProperties(sources, [sink], tolerance)
	if tranVertices == True:
		stlSinkVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		if sink.Type() == topologic.Vertex.Type():
			stlSinkVertices.push_back(sink)
		elif hidimSink >= topologic.Vertex.Type():
			sink.Vertices(stlSinkVertices)
			sinkVertices = list(stlSinkVertices)
		_ = transferCustomProperties(sources, sinkVertices, tolerance)
	if tranEdges == True:
		stlSinkEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		if sink.Type() == topologic.Edge.Type():
			stlSinkEdges.push_back(sink)
		elif hidimSink >= topologic.Edge.Type():
			sink.Edges(stlSinkEdges)
			sinkEdges = list(stlSinkEdges)
		_ = transferCustomProperties(sources, sinkEdges, tolerance)
	if tranFaces == True:
		stlSinkFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		if sink.Type() == topologic.Face.Type():
			stlSinkFaces.push_back(sink)
		elif hidimSink >= topologic.Face.Type():
			sink.Faces(stlSinkFaces)
			sinkFaces = list(stlSinkFaces)
		_ = transferCustomProperties(sources, sinkFaces, tolerance)
	if tranCells == True:
		stlSinkCells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		if sink.Type() == topologic.Cell.Type():
			stlSinkCells.push_back(sink)
		elif hidimSink >= topologic.Cell.Type():
			sink.Cells(stlSinkCells)
			sinkCells = list(stlSinkCells)
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
