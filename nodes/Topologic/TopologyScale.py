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
	cellSels = cellSelectors(topology)
	faceSels = faceSelectors(topology)
	edgeSels = edgeSelectors(topology)
	vertexSels = vertexSelectors(topology)
	cellSels_new = []
	faceSels_new = []
	edgeSels_new = []
	vertexSels_new = []
	for cellSel in cellSels:
		cellSels_new.append(topologic.TopologyUtility.Scale(cellSel, origin, x, y, z))
	faceSels_new = []
	for faceSel in faceSels:
		faceSels_new.append(topologic.TopologyUtility.Scale(faceSel, origin, x, y, z))
	for edgeSel in edgeSels:
		edgeSels_new.append(topologic.TopologyUtility.Scale(edgeSel, origin, x, y, z))
	for vertexSel in vertexSels:
		vertexSels_new.append(topologic.TopologyUtility.Scale(vertexSel, origin, x, y, z))
	topology_new = topologic.TopologyUtility.Scale(topology, origin, x, y, z)
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

class SvTopologyScale(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Scales the input Topology based on the input origin, and X, Y, Z scale factors    
	"""
	bl_idname = 'SvTopologyScale'
	bl_label = 'Topology.Scale'
	bl_icon = 'SELECT_DIFFERENCE'
	XFactor: FloatProperty(name="XFactor", default=1, precision=4, update=updateNode)
	YFactor: FloatProperty(name="YFactor",  default=1, precision=4, update=updateNode)
	ZFactor: FloatProperty(name="ZFactor",  default=1, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.width = 175
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'XFactor').prop_name = 'XFactor'
		self.inputs.new('SvStringsSocket', 'YFactor').prop_name = 'YFactor'
		self.inputs.new('SvStringsSocket', 'ZFactor').prop_name = 'ZFactor'
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
	bpy.utils.register_class(SvTopologyScale)

def unregister():
	bpy.utils.unregister_class(SvTopologyScale)
