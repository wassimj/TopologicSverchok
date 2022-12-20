import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from mathutils import Vector

from . import Replication
from . import TopologyTransferDictionariesBySelectors

def update_sockets(self, context):
	# hide all input sockets
	self.inputs['X'].hide_safe = True
	self.inputs['Y'].hide_safe = True
	self.inputs['Z'].hide_safe = True
	self.inputs['Direction'].hide_safe = True
	self.inputs['Distance'].hide_safe = True

	if self.InputMode == "XYZ":
		self.inputs['X'].hide_safe = False
		self.inputs['Y'].hide_safe = False
		self.inputs['Z'].hide_safe = False
	else:
		self.inputs['Direction'].hide_safe = False
		self.inputs['Distance'].hide_safe = False
	updateNode(self, context)

def cellSelectors(topology):
	cells = []
	try:
		_ = topology.Cells(None, cells)
	except:
		cells = []
	selectors = []
	for aCell in cells:
		dict = aCell.GetDictionary()
		selector = topologic.CellUtility.InternalVertex(aCell, 0.0001)
		if len(dict.Keys()) > 0:
			_ = selector.SetDictionary(dict)
		selectors.append(selector)
	return selectors

def faceSelectors(topology):
	faces = []
	try:
		_ = topology.Faces(None, faces)
	except:
		faces = []
	selectors = []
	for aFace in faces:
		dict = aFace.GetDictionary()
		selector = topologic.FaceUtility.InternalVertex(aFace, 0.0001)
		if len(dict.Keys()) > 0:
			_ = selector.SetDictionary(dict)
		selectors.append(selector)
	return selectors

def edgeSelectors(topology):
	edges = []
	try:
		_ = topology.Edges(None, edges)
	except:
		edges = []
	selectors = []
	for anEdge in edges:
		dict = anEdge.GetDictionary()
		selector = topologic.EdgeUtility.PointAtParameter(anEdge, 0.5)
		if len(dict.Keys()) > 0:
			_ = selector.SetDictionary(dict)
		selectors.append(selector)
	return selectors

def vertexSelectors(topology):
	vertices = []
	try:
		_ = topology.Vertices(None, vertices)
	except:
		vertices = []
	selectors = []
	for aVertex in vertices:
		dict = aVertex.GetDictionary()
		selector = aVertex
		if len(dict.Keys()) > 0:
			_ = selector.SetDictionary(dict)
		selectors.append(selector)
	return selectors

def processItem(item):
	topology = item[0]
	x = item[1]
	y = item[2]
	z = item[3]
	cellSels = cellSelectors(topology)
	faceSels = faceSelectors(topology)
	edgeSels = edgeSelectors(topology)
	vertexSels = vertexSelectors(topology)
	cellSels_new = []
	faceSels_new = []
	edgeSels_new = []
	vertexSels_new = []
	for cellSel in cellSels:
		cellSels_new.append(topologic.TopologyUtility.Translate(cellSel, x, y, z))
	faceSels_new = []
	for faceSel in faceSels:
		faceSels_new.append(topologic.TopologyUtility.Translate(faceSel, x, y, z))
	for edgeSel in edgeSels:
		edgeSels_new.append(topologic.TopologyUtility.Translate(edgeSel, x, y, z))
	for vertexSel in vertexSels:
		vertexSels_new.append(topologic.TopologyUtility.Translate(vertexSel, x, y, z))
	topology_new = topologic.TopologyUtility.Translate(topology, x, y, z)
	if len(cellSels_new) > 0:
		topology_new = TopologyTransferDictionariesBySelectors.processItem(cellSels_new, topology_new, False, False, False, True, 0.0001)
	if len(faceSels_new) > 0:
		topology_new = TopologyTransferDictionariesBySelectors.processItem(faceSels_new, topology_new, False, False, True, False, 0.0001)
	if len(edgeSels_new) > 0:
		topology_new = TopologyTransferDictionariesBySelectors.processItem(edgeSels_new, topology_new, False, True, False, False, 0.0001)
	if len(vertexSels_new) > 0:
		topology_new = TopologyTransferDictionariesBySelectors.processItem(vertexSels_new, topology_new, True, False, False, False, 0.0001)
	return topology_new

def processDirectionDistance(item):
	topology = item[0]
	direction = item[1]
	distance = item[2]
	print("Direction", direction)
	dir_vec = Vector((direction[0], direction[1], direction[2]))
	dir_vec.normalize()
	offset = dir_vec*distance
	return processItem([topology, offset[0], offset[1], offset[2]])

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
input_items = [("XYZ", "XYZ", "", 1),("Direction/Distance", "Direction/Distance", "", 2)]

class SvTopologyTranslate(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Translates the input Topology based on the input X,Y,Z translation values    
	"""
	bl_idname = 'SvTopologyTranslate'
	bl_label = 'Topology.Translate'
	bl_icon = 'SELECT_DIFFERENCE'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=0, precision=4, update=updateNode)
	Distance: FloatProperty(name="Distance",  default=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	InputMode : EnumProperty(name='Input Mode', description='The input component format of the data', items=input_items, default="XYZ", update=update_sockets)

	def sv_init(self, context):
		self.width = 175
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.inputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.inputs.new('SvStringsSocket', 'Z').prop_name = 'Z'
		self.inputs.new('SvStringsSocket', 'Direction')
		self.inputs.new('SvStringsSocket', 'Distance').prop_name = 'Distance'
		self.outputs.new('SvStringsSocket', 'Topology')
		update_sockets(self, context)
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		if not socket.hide_safe:
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
		split.row().label(text="Input Mode")
		split.row().prop(self, "InputMode", expand=False, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		topologyList = Replication.flatten(topologyList)
		if self.InputMode == "XYZ":
			xList = self.inputs['X'].sv_get(deepcopy=True)
			yList = self.inputs['Y'].sv_get(deepcopy=True)
			zList = self.inputs['Z'].sv_get(deepcopy=True)
			xList = Replication.flatten(xList)
			yList = Replication.flatten(yList)
			zList = Replication.flatten(zList)
			inputs = [topologyList, xList, yList, zList]
			if ((self.Replication) == "Trim"):
				inputs = Replication.trim(inputs)
				inputs = Replication.transposeList(inputs)
			elif (((self.Replication) == "Iterate")  or ((self.Replication) == "Default")):
				inputs = Replication.iterate(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Repeat"):
				inputs = Replication.repeat(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Interlace"):
				inputs = list(Replication.interlace(inputs))
			outputs = []
			for anInput in inputs:
				outputs.append(processItem(anInput))
		else:
			directionList = self.inputs['Direction'].sv_get(deepcopy=True)
			#directionList = flatten(directionList)
			distanceList = self.inputs['Distance'].sv_get(deepcopy=True)
			distanceList = Replication.flatten(distanceList)
			inputs = [topologyList, directionList, distanceList]
			if ((self.Replication) == "Trim"):
				inputs = Replication.trim(inputs)
				inputs = Replication.transposeList(inputs)
			elif (((self.Replication) == "Iterate")  or ((self.Replication) == "Default")):
				inputs = Replication.iterate(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Repeat"):
				inputs = Replication.repeat(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Interlace"):
				inputs = list(Replication.interlace(inputs))
			outputs = []
			for anInput in inputs:
				outputs.append(processDirectionDistance(anInput))
		outputs = Replication.unflatten(outputs, self.inputs['Topology'].sv_get(deepcopy=True))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyTranslate)

def unregister():
	bpy.utils.unregister_class(SvTopologyTranslate)
