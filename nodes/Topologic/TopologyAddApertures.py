import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import cppyy
import time

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

def isInside(aperture, face, tolerance):
	return (topologic.VertexUtility.Distance(aperture.Topology.Centroid(), face) < tolerance)

def internalVertex(topology, tolerance):
	topology = fixTopologyClass(topology)
	vst = None
	classType = topology.GetType()
	if classType == 64: #CellComplex
		tempCells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		_ = topology.Cells(tempCells)
		tempCell = tempCells.front()
		vst = topologic.CellUtility.InternalVertex(tempCell, tolerance)
	elif classType == 32: #Cell
		vst = topologic.CellUtility.InternalVertex(topology, tolerance)
	elif classType == 16: #Shell
		tempFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = topology.Faces(tempFaces)
		tempFace = tempFaces.front()
		vst = topologic.FaceUtility.InternalVertex(tempFace, tolerance)
	elif classType == 8: #Face
		vst = topologic.FaceUtility.InternalVertex(topology, tolerance)
	elif classType == 4: #Wire
		if topology.IsClosed():
			internalBoundaries = cppyy.gbl.std.list[topologic.Wire.Ptr]()
			tempFace = topologic.Face.ByExternalInternalBoundaries(topology, internalBoundaries)
			vst = topologic.FaceUtility.InternalVertex(tempFace, tolerance)
		else:
			tempEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = topology.Edges(tempEdges)
			vst = topologic.EdgeUtility.PointAtParameter(tempVertex.front(), 0.5)
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

def processItem(item):
	topology = item[0]
	apertures = item[1]
	exclusive = item[2]
	tolerance = item[3]
	subTopologyType = item[4]
	subTopologies = []
	if subTopologyType == "Face":
		faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = topology.Faces(faces)
		subTopologies = list(faces)
	elif subTopologyType == "Edge":
		edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		_ = topology.Edges(edges)
		subTopologies = list(edges)
	elif subTopologyType == "Vertex":
		vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = topology.Vertices(vertices)
		subTopologies = list(vertices)
	processApertures(subTopologies, apertures, exclusive, tolerance)
	return topology

def matchLengths(list):
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

topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Face", "Face", "", 3)]

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

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Apertures')
		self.inputs.new('SvStringsSocket', 'Exclusive').prop_name = 'Exclusive'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Topology')

	def draw_buttons(self, context, layout):
		layout.prop(self, "subtopologyType",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		aperturesList = self.inputs['Apertures'].sv_get(deepcopy=True)
		exclusiveList = self.inputs['Exclusive'].sv_get(deepcopy=True)[0]
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)[0]
		if isinstance(aperturesList[0], list) == False:
			aperturesList = [aperturesList]
		subTopologiesList = [self.subtopologyType]
		matchLengths([topologyList, aperturesList, exclusiveList, toleranceList, subTopologiesList])
		inputs = zip(topologyList, aperturesList, exclusiveList, toleranceList, subTopologiesList)
		output = []
		for anInput in inputs:
			output.append(processItem(anInput))
		self.outputs['Topology'].sv_set(output)
		end = time.time()
		print("Topology.AddApertures Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyAddApertures)

def unregister():
    bpy.utils.unregister_class(SvTopologyAddApertures)
