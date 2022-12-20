import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from . import Replication
from . import TopologyTransferDictionariesBySelectors

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
	origin = item[1]
	x = item[2]
	y = item[3]
	z = item[4]
	degree = item[5]
	cellSels = cellSelectors(topology)
	faceSels = faceSelectors(topology)
	edgeSels = edgeSelectors(topology)
	vertexSels = vertexSelectors(topology)
	cellSels_new = []
	faceSels_new = []
	edgeSels_new = []
	vertexSels_new = []
	for cellSel in cellSels:
		cellSels_new.append(topologic.TopologyUtility.Rotate(cellSel, origin, x, y, z, degree))
	faceSels_new = []
	for faceSel in faceSels:
		faceSels_new.append(topologic.TopologyUtility.Rotate(faceSel, origin, x, y, z, degree))
	for edgeSel in edgeSels:
		edgeSels_new.append(topologic.TopologyUtility.Rotate(edgeSel, origin, x, y, z, degree))
	for vertexSel in vertexSels:
		vertexSels_new.append(topologic.TopologyUtility.Rotate(vertexSel, origin, x, y, z, degree))
	topology_new = topologic.TopologyUtility.Rotate(topology, origin, x, y, z, degree)
	if len(cellSels_new) > 0:
		topology_new = TopologyTransferDictionariesBySelectors.processItem(cellSels_new, topology_new, False, False, False, True, 0.0001)
	if len(faceSels_new) > 0:
		topology_new = TopologyTransferDictionariesBySelectors.processItem(faceSels_new, topology_new, False, False, True, False, 0.0001)
	if len(edgeSels_new) > 0:
		topology_new = TopologyTransferDictionariesBySelectors.processItem(edgeSels_new, topology_new, False, True, False, False, 0.0001)
	if len(vertexSels_new) > 0:
		topology_new = TopologyTransferDictionariesBySelectors.processItem(vertexSels_new, topology_new, True, False, False, False, 0.0001)
	return topology_new

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvTopologyRotate(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Rotates the input Topology based on the input rotation origin, axis of rotation, and degrees    
	"""
	bl_idname = 'SvTopologyRotate'
	bl_label = 'Topology.Rotate'
	bl_icon = 'SELECT_DIFFERENCE'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=1, precision=4, update=updateNode)
	Degree: FloatProperty(name="Degree",  default=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.width = 175
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.inputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.inputs.new('SvStringsSocket', 'Z').prop_name = 'Z'
		self.inputs.new('SvStringsSocket', 'Degree').prop_name = 'Degree'
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

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return

		inputs_nested = []
		inputs_flat = []
		for anInput in self.inputs:
			if anInput == self.inputs['Origin']:
				if not anInput.is_linked:
					inp = topologic.Vertex.ByCoordinates(0,0,0)
				else:
					inp = anInput.sv_get(deepcopy=True)
			else:
				inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		inputs_replicated = Replication.replicateInputs(inputs_flat.copy(), self.Replication)
		outputs = []
		for anInput in inputs_replicated:
			outputs.append(processItem(anInput))
		inputs_flat = []
		for anInput in self.inputs:
			if anInput == self.inputs['Origin']:
				if not anInput.is_linked:
					inp = topologic.Vertex.ByCoordinates(0,0,0)
				else:
					inp = anInput.sv_get(deepcopy=True)
			else:
				inp = anInput.sv_get(deepcopy=True)
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			outputs = Replication.re_interlace(outputs, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			outputs = Replication.unflatten(outputs, match_list)
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyRotate)

def unregister():
	bpy.utils.unregister_class(SvTopologyRotate)
