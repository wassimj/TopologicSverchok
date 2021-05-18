import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty
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
		if typeFilter == "Vertex":
			topologies = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			_ = topology.Vertices(topologies)
		elif typeFilter == "Edge":
			topologies = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = topology.Edges(topologies)
		elif typeFilter == "Face":
			topologies = cppyy.gbl.std.list[topologic.Face.Ptr]()
			_ = topology.Faces(topologies)
		elif typeFilter == "Cell":
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

topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Face", "Face", "", 3), ("Cell", "Cell", "", 4)]
replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvTopologyExplode(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Pulls apart (explodes) the sub-topologies of the input Topology based on the input origin, scale factor, and topology type filter
	"""
	bl_idname = 'SvTopologyExplode'
	bl_label = 'Topology.Explode'
	Scale: FloatProperty(name="Scale", default=1.5, min=1.0, precision=4, update=updateNode)
	Type: EnumProperty(name="Type", description="Specify subtopology type", default="Face", items=topologyTypes, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Scale').prop_name='Scale'
		self.inputs.new('SvStringsSocket', 'Type').prop_name = 'Type'
		self.outputs.new('SvStringsSocket', 'Topology')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = flatten(self.inputs['Topology'].sv_get(deepcopy=False))
		if not (self.inputs['Origin'].is_linked):
			originList = [topologic.Vertex.ByCoordinates(0,0,0)]
		else:
			originList = flatten(self.inputs['Origin'].sv_get(deepcopy=True))
		scaleList = flatten(self.inputs['Scale'].sv_get(deepcopy=True))
		typeList = flatten(self.inputs['Type'].sv_get(deepcopy=True))
		inputs = [topologyList, originList, scaleList, typeList]
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

def register():
	bpy.utils.register_class(SvTopologyExplode)

def unregister():
	bpy.utils.unregister_class(SvTopologyExplode)
