import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
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

def processApertures(subTopologies, apertureCluster, exclusive, tolerance):
	apertures = []
	cells = []
	faces = []
	edges = []
	vertices = []
	_ = apertureCluster.Cells(None, cells)
	_ = apertureCluster.Faces(None, faces)
	_ = apertureCluster.Vertices(None, vertices)
	# apertures are assumed to all be of the same topology type.
	if len(cells) > 0:
		apertures = cells
	elif len(faces) > 0:
		apertures = faces
	elif len(edges) > 0:
		apertures = edges
	elif len(vertices) > 0:
		apertures = vertices
	else:
		apertures = []
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

def processItem(item):
	topology = item[0].DeepCopy()
	apertureCluster = item[1]
	exclusive = item[2]
	tolerance = item[3]
	subTopologyType = item[4]
	subTopologies = []
	if subTopologyType == "Face":
		_ = topology.Faces(None, subTopologies)
	elif subTopologyType == "Edge":
		_ = topology.Edges(None, subTopologies)
	elif subTopologyType == "Vertex":
		_ = topology.Vertices(None, subTopologies)
	processApertures(subTopologies, apertureCluster, exclusive, tolerance)
	return topology

topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Face", "Face", "", 3)]
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]


class SvTopologyAddApertures(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Adds the input Apertures to the input Topology    
	"""
	bl_idname = 'SvTopologyAddApertures'
	bl_label = 'Topology.AddApertures'
	Exclusive: BoolProperty(name="Exclusive", default=True, update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)
	subtopologyType: EnumProperty(name="Apply To:", description="Specify subtopology type to apply the apertures to", default="Face", items=topologyTypes, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Aperture Cluster')
		self.inputs.new('SvStringsSocket', 'Exclusive').prop_name = 'Exclusive'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Topology')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "subtopologyType",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		aperturesList = self.inputs['Aperture Cluster'].sv_get(deepcopy=True)
		exclusiveList = self.inputs['Exclusive'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)

		topologyList = flatten(topologyList)
		aperturesList = flatten(aperturesList)
		exclusiveList = flatten(exclusiveList)
		toleranceList = flatten(toleranceList)
		subTopologiesList = [self.subtopologyType]
		inputs = [topologyList, aperturesList, exclusiveList, toleranceList, subTopologiesList]
		if ((self.Replication) == "Default"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
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
		print("Topology.AddApertures Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyAddApertures)

def unregister():
    bpy.utils.unregister_class(SvTopologyAddApertures)
