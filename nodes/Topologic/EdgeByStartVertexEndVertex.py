import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def processItem(item):
	sv = item[0]
	ev = item[1]
	tol = item[2]
	edge = None
	if not sv or not ev:
		return None
	if topologic.Topology.IsSame(sv, ev):
		return None
	if topologic.VertexUtility.Distance(sv, ev) < tol:
		return None
	try:
		edge = topologic.Edge.ByStartVertexEndVertex(sv, ev)
	except:
		edge = None
	return edge

replication = [("Default", "Default", "", 1), ("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvEdgeByStartVertexEndVertex(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates an Edge from the input Vertices
	"""
	bl_idname = 'SvEdgeByStartVertexEndVertex'
	bl_label = 'Edge.ByStartVertexEndVertex'
	bl_icon = 'SELECT_DIFFERENCE'

	startVertex: StringProperty(name="StartVertex", update=updateNode)
	endVertex: StringProperty(name="EndVertex", update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'StartVertex')
		self.inputs.new('SvStringsSocket', 'EndVertex')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Edge')
		self.width = 225
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
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			outputs = Replication.re_interlace(outputs, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			outputs = Replication.unflatten(outputs, match_list)
		self.outputs['Edge'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvEdgeByStartVertexEndVertex)

def unregister():
    bpy.utils.unregister_class(SvEdgeByStartVertexEndVertex)
