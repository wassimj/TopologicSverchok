import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time
from . import Replication

def boundingBox(cell):
	vertices = []
	_ = cell.Vertices(None, vertices)
	x = []
	y = []
	z = []
	for aVertex in vertices:
		x.append(aVertex.X())
		y.append(aVertex.Y())
		z.append(aVertex.Z())
	return ([min(x), min(y), min(z), max(x), max(y), max(z)])

def processItem(input):
	vertex, topology, exclusive, tolerance = input
	if isinstance(topology, topologic.Cell):
		cells = [topology]
	elif isinstance(topology, topologic.Cluster) or isinstance(topology, topologic.CellComplex):
		cells = []
		_ = topology.Cells(None, cells)
	else:
		raise Exception("Vertex.EnclosingCell - Error: Input topology does not contain any Cells.")
	if len(cells) < 1:
		raise Exception("Vertex.EnclosingCell - Error: Input topology does not contain any Cells.")
	enclosingCells = []
	for i in range(len(cells)):
		bbox = boundingBox(cells[i])
		minX = bbox[0]
		if ((vertex.X() < bbox[0]) or (vertex.Y() < bbox[1]) or (vertex.Z() < bbox[2]) or (vertex.X() > bbox[3]) or (vertex.Y() > bbox[4]) or (vertex.Z() > bbox[5])) == False:
			if topologic.CellUtility.Contains(cells[i], vertex, tolerance) == 0:
				if exclusive:
					return([cells[i]])
				else:
					enclosingCells.append(cells[i])
	return enclosingCells

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvVertexEnclosingCell(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Cell that contains the input Vertex from the list of input CellCluster
	"""
	bl_idname = 'SvVertexEnclosingCell'
	bl_label = 'Vertex.EnclosingCell'
	bl_icon = 'SELECT_DIFFERENCE'

	Exclusive: BoolProperty(name="Exclusive", default=True, update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.width = 175
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Exclusive').prop_name = 'Exclusive'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Cell')
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
			for anOutput in self.outputs:
				anOutput.sv_set([])
			return
		inputs_nested = []
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		inputs_replicated = Replication.replicateInputs(inputs_flat, self.Replication)
		outputs = []
		for anInput in inputs_replicated:
			outputs.append(processItem(anInput))
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			outputs = Replication.re_interlace(outputs, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			outputs = Replication.unflatten(outputs, match_list)
		if len(outputs) == 1:
			if isinstance(outputs[0], list):
				outputs = outputs[0]
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvVertexEnclosingCell)

def unregister():
	bpy.utils.unregister_class(SvVertexEnclosingCell)
