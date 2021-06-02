import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

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

def getKeys(item):
	stl_keys = item.Keys()
	returnList = []
	copyKeys = stl_keys.__class__(stl_keys) #wlav suggested workaround. Make a copy first
	for x in copyKeys:
		k = x.c_str()
		returnList.append(k)
	return returnList

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
					sourceKeys = getKeys(d)
					for aSourceKey in sourceKeys:
						if aSourceKey not in sinkKeys:
							sinkKeys.append(aSourceKey)
							sinkValues.append("")
					for i in range(len(sourceKeys)):
						index = sinkKeys.index(sourceKeys[i])
						k = cppyy.gbl.std.string(sourceKeys[i])
						sourceValue = d.ValueAtKey(k).Value()
						if sourceValue != None:
							if (isinstance(sourceValue, cppyy.gbl.std.string)):
								sourceValue = sourceValue.c_str()
							if sinkValues[index] != "":
								if isinstance(sinkValues[index], list):
									sinkValues[index].append(sourceValue)
								else:
									sinkValues[index] = [sinkValues[index], sourceValue]
							else:
								sinkValues[index] = sourceValue
		if len(sinkKeys) > 0 and len(sinkValues) > 0:
			stlKeys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
			for sinkKey in sinkKeys:
				stlKeys.push_back(sinkKey)
			stlValues = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
			for sinkValue in sinkValues:
				if isinstance(sinkValue, bool):
					stlValues.push_back(topologic.IntAttribute(sinkValue))
				elif isinstance(sinkValue, int):
					stlValues.push_back(topologic.IntAttribute(sinkValue))
				elif isinstance(sinkValue, float):
					stlValues.push_back(topologic.DoubleAttribute(sinkValue))
				elif isinstance(sinkValue, str):
					stlValues.push_back(topologic.StringAttribute(sinkValue))
				elif isinstance(sinkValue, list):
					l = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
					for v in sinkValue:
						if isinstance(v, bool):
							l.push_back(topologic.IntAttribute(v))
						elif isinstance(v, int):
							l.push_back(topologic.IntAttribute(v))
						elif isinstance(v, float):
							l.push_back(topologic.DoubleAttribute(v))
						elif isinstance(v, str):
							l.push_back(topologic.StringAttribute(v))
					stlValues.push_back(topologic.ListAttribute(l))
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

class SvTopologyTransferDictionaries(bpy.types.Node, SverchCustomTreeNode):

	"""
	Triggers: Topologic
	Tooltip: Transfers the Dictionaries of the source Topologies to the sink Topology based on specified options
	"""
	bl_idname = 'SvTopologyTransferDictionaries'
	bl_label = 'Topology.TransferDictionaries'
	TransferVertexDicts: BoolProperty(name="Transfer Vertex Dicts", default=True, update=updateNode)
	TransferEdgeDicts: BoolProperty(name="Transfer Edge Dicts", default=True, update=updateNode)
	TransferFaceDicts: BoolProperty(name="Transfer Face Dicts", default=True, update=updateNode)
	TransferCellDicts: BoolProperty(name="Transfer Cell Dicts", default=True, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Sources')
		self.inputs.new('SvStringsSocket', 'Sink')
		self.inputs.new('SvStringsSocket', 'Transfer Vertex Dicts').prop_name = 'TransferVertexDicts'
		self.inputs.new('SvStringsSocket', 'Transfer Edge Dicts').prop_name = 'TransferEdgeDicts'
		self.inputs.new('SvStringsSocket', 'Transfer Face Dicts').prop_name = 'TransferFaceDicts'
		self.inputs.new('SvStringsSocket', 'Transfer Cell Dicts').prop_name = 'TransferCellDicts'
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
		tranVertexDicts = self.inputs['Transfer Vertex Dicts'].sv_get(deepcopy=False)[0][0]
		tranEdgeDicts = self.inputs['Transfer Edge Dicts'].sv_get(deepcopy=False)[0][0]
		tranFaceDicts = self.inputs['Transfer Face Dicts'].sv_get(deepcopy=False)[0][0]
		tranCellDicts = self.inputs['Transfer Cell Dicts'].sv_get(deepcopy=False)[0][0]
		tolerance = self.inputs['Tolerance'].sv_get(deepcopy=False)[0][0]
		output = processItem(sources, sink, tranVertexDicts, tranEdgeDicts, tranFaceDicts, tranCellDicts, tolerance)
		self.outputs['Sink'].sv_set([output])
		end = time.time()
		print("Topology.TransferDictionaries Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyTransferDictionaries)

def unregister():
    bpy.utils.unregister_class(SvTopologyTransferDictionaries)
