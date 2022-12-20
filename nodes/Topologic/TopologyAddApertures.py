import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication
from . import VertexNearestTopology, DictionaryByKeysValues, DictionaryValueAtKey

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
	cells = []
	faces = []
	edges = []
	vertices = []
	apertures = []
	if not apertureCluster:
		return None
	_ = apertureCluster.Cells(None, cells)
	_ = apertureCluster.Faces(None, faces)
	_ = apertureCluster.Edges(None, edges)
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
	topologyType = subTopologies[0].GetTypeAsString()
	tempTopologies = []
	for i in range(len(subTopologies)):
		usedTopologies.append(0)
		d = DictionaryByKeysValues.processItem([["index"], [i]])
		tempTopology = subTopologies[i].DeepCopy()
		_ = tempTopology.SetDictionary(d)
		tempTopologies.append(tempTopology)
	cluster = topologic.Cluster.ByTopologies(tempTopologies)
	for aperture in apertures:
		apCenter = internalVertex(aperture, tolerance)
		nearestTempTopology = VertexNearestTopology.processItem([apCenter, cluster, False, topologyType])
		index = DictionaryValueAtKey.processItem([nearestTempTopology.GetDictionary(), "index"])
		nearestTopology = subTopologies[index]
		if exclusive == True and usedTopologies[i] == 1:
			continue
		context = topologic.Context.ByTopologyParameters(nearestTopology, 0.5, 0.5, 0.5)
		_ = topologic.Aperture.ByTopologyContext(aperture, context)
		if exclusive == True:
			usedTopologies[i] = 1
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

class SvTopologyAddApertures(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Adds the input Apertures to the input Topology    
	"""
	bl_idname = 'SvTopologyAddApertures'
	bl_label = 'Topology.AddApertures'
	bl_icon = 'SELECT_DIFFERENCE'
	Exclusive: BoolProperty(name="Exclusive", default=True, update=updateNode)
	subtopologyType: EnumProperty(name="Apply To:", description="Specify subtopology type to apply the apertures to", default="Face", items=topologyTypes, update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.width = 200
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Aperture Cluster')
		self.inputs.new('SvStringsSocket', 'Exclusive').prop_name = 'Exclusive'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Topology')
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Replication")
		split.row().prop(self, "Replication",text="")
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Apply To")
		split.row().prop(self, "subtopologyType",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Distance'].sv_set([])
			return
		inputs_nested = []
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		inputs_nested.append([self.subtopologyType])
		inputs_flat.append([self.subtopologyType])
		inputs_replicated = Replication.replicateInputs(inputs_flat.copy(), self.Replication)
		outputs = []
		for anInput in inputs_replicated:
			outputs.append(processItem(anInput))
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_flat.append(Replication.flatten(inp))
		inputs_flat.append([self.subtopologyType])
		if self.Replication == "Interlace":
			outputs = Replication.re_interlace(outputs, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			outputs = Replication.unflatten(outputs, match_list)
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvTopologyAddApertures)

def unregister():
    bpy.utils.unregister_class(SvTopologyAddApertures)
