import bpy
from bpy.props import FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def projectVertex(vertex, face, vList):
	if topologic.FaceUtility.IsInside(face, vertex, 0.001):
		return vertex
	d = topologic.VertexUtility.Distance(vertex, face)*10
	far_vertex = topologic.TopologyUtility.Translate(vertex, vList[0]*d, vList[1]*d, vList[2]*d)
	if topologic.VertexUtility.Distance(vertex, far_vertex) > 0.001:
		e = topologic.Edge.ByStartVertexEndVertex(vertex, far_vertex)
		pv = face.Intersect(e, False)
		return pv
	else:
		return None

def processItem(item):
	wire, face, direction = item
	large_face = topologic.TopologyUtility.Scale(face, face.CenterOfMass(), 500, 500, 500)
	try:
		vList = [direction.X(), direction.Y(), direction.Z()]
	except:
		try:
			vList = [direction[0], direction[1], direction[2]]
		except:
			raise Exception("Wire.Project - Error: Could not get the vector from the input direction")
	projected_wire = None
	edges = []
	_ = wire.Edges(None, edges)
	projected_edges = []

	if large_face:
		if (large_face.Type() == topologic.Face.Type()):
			for edge in edges:
				if edge:
					if (edge.Type() == topologic.Edge.Type()):
						sv = edge.StartVertex()
						ev = edge.EndVertex()

						psv = projectVertex(sv, large_face, direction)
						pev = projectVertex(ev, large_face, direction)
						if psv and pev:
							try:
								pe = topologic.Edge.ByStartVertexEndVertex(psv, pev)
								projected_edges.append(pe)
							except:
								continue
	w = topologic.Wire.ByEdges(projected_edges)
	return w

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvWireProject(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Projects the input Wire on the input Face
	"""
	bl_idname = 'SvWireProject'
	bl_label = 'Wire.Project'
	bl_icon = 'SELECT_DIFFERENCE'

	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'Direction')
		self.outputs.new('SvStringsSocket', 'Wire')
		self.width = 175
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
		if len(outputs) == 1:
			if isinstance(outputs[0], list):
				outputs = outputs[0]
		self.outputs['Wire'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvWireProject)

def unregister():
	bpy.utils.unregister_class(SvWireProject)
