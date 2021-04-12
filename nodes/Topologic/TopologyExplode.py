import bpy
from bpy.props import StringProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import cppyy

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

def create_stl_list(cppyy_data_type):
    values = cppyy.gbl.std.list[cppyy_data_type]()
    return values

def convert_to_stl_list(py_list, cppyy_data_type):
    values = create_stl_list(cppyy_data_type)
    for i in py_list:
        values.push_back(i)
    return values

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

def processItem(item):
	topology = item[0]
	origin = item[1]
	scale = item[2]
	typeFilter = item[3]
	topologies = []
	newTopologies = cppyy.gbl.std.list[topologic.Topology.Ptr]()
	cluster = None
	if topology.__class__ == topologic.Graph:
		graphTopology = fixTopologyClass(topology.Topology())
		graphEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		_ = graphTopology.Edges(graphEdges)
		for anEdge in graphEdges:
			sv = anEdge.StartVertex()
			oldX = sv.X()
			oldY = sv.Y()
			oldZ = sv.Z()
			newX = (oldX - origin.X())*scale + origin.X()
			newY = (oldY - origin.Y())*scale + origin.Y()
			newZ = (oldZ - origin.Z())*scale + origin.Z()
			newSv = topologic.Vertex.ByCoordinates(newX, newY, newZ)
			ev = anEdge.EndVertex()
			oldX = ev.X()
			oldY = ev.Y()
			oldZ = ev.Z()
			newX = (oldX - origin.X())*scale + origin.X()
			newY = (oldY - origin.Y())*scale + origin.Y()
			newZ = (oldZ - origin.Z())*scale + origin.Z()
			newEv = topologic.Vertex.ByCoordinates(newX, newY, newZ)
			newEdge = topologic.Edge.ByStartVertexEndVertex(newSv, newEv)
			newTopologies.push_back(newEdge)
		cluster = topologic.Cluster.ByTopologies(newTopologies)
	else:
		if typeFilter == topologic.Vertex.Type():
			topologies = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			_ = topology.Vertices(topologies)
		elif typeFilter == topologic.Edge.Type():
			topologies = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = topology.Edges(topologies)
		elif typeFilter == topologic.Face.Type():
			topologies = cppyy.gbl.std.list[topologic.Face.Ptr]()
			_ = topology.Faces(topologies)
		elif typeFilter == topologic.Cell.Type():
			topologies = cppyy.gbl.std.list[topologic.Cell.Ptr]()
			_ = topology.Cells(topologies)
		else:
			topologies = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			_ = topology.Vertices(topologies)
		for aTopology in topologies:
			c = relevantSelector(aTopology)
			oldX = c.X()
			oldY = c.Y()
			oldZ = c.Z()
			newX = (oldX - origin.X())*scale + origin.X()
			newY = (oldY - origin.Y())*scale + origin.Y()
			newZ = (oldZ - origin.Z())*scale + origin.Z()
			xT = newX - oldX
			yT = newY - oldY
			zT = newZ - oldZ
			newTopology = topologic.TopologyUtility.Translate(aTopology, xT, yT, zT)
			newTopologies.push_back(newTopology)
		cluster = topologic.Cluster.ByTopologies(newTopologies)
	return cluster

class SvTopologyExplode(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Pulls apart (explodes) the sub-topologies of the input Topology based on the input origin, scale factor, and topology type filter
	"""
	bl_idname = 'SvTopologyExplode'
	bl_label = 'Topology.Explode'
	TypeFilter: IntProperty(name="Type Filter", default=255, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Scale')
		self.inputs.new('SvStringsSocket', 'Type Filter').prop_name = 'TypeFilter'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = flatten(self.inputs['Topology'].sv_get(deepcopy=False))
		originList = flatten(self.inputs['Origin'].sv_get(deepcopy=False))
		scaleList = flatten(self.inputs['Scale'].sv_get(deepcopy=False))
		typeFilterList = flatten(self.inputs['Type Filter'].sv_get(deepcopy=False))
		maxLength = max([len(topologyList), len(originList), len(scaleList), len(typeFilterList)])
		for i in range(len(topologyList), maxLength):
			topologyList.append(topologyList[-1])
		for i in range(len(originList), maxLength):
			originList.append(originList[-1])
		for i in range(len(scaleList), maxLength):
			scaleList.append(scaleList[-1])
		for i in range(len(typeFilterList), maxLength):
			typeFilterList.append(typeFilterList[-1])
		inputs = []
		if (len(topologyList) == len(originList) == len(scaleList) == len(typeFilterList)):
			inputs = zip(topologyList, originList, scaleList, typeFilterList)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyExplode)

def unregister():
	bpy.utils.unregister_class(SvTopologyExplode)
