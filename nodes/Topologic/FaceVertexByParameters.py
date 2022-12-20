import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def processItem(item):
	face, u, v = item
	vertex = topologic.FaceUtility.VertexAtParameters(face, u, v)
	return vertex

def recur(item):
	output = []
	if item == None:
		return []
	if isinstance(item[0], list):
		for subItem in item:
			output.append(recur(subItem))
	else:
		output = processItem(item)
	return output

replication = [("Default", "Default", "", 1), ("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvFaceVertexByParameters(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Creates a Vertex on the input Face at the input UV parameters    
	"""
	bl_idname = 'SvFaceVertexByParameters'
	bl_label = 'Face.VertexByParameters'
	bl_icon = 'SELECT_DIFFERENCE'
	U: FloatProperty(name="U", default=0.5, precision=4, update=updateNode)
	V: FloatProperty(name="V",  default=0.5, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'U').prop_name = 'U'
		self.inputs.new('SvStringsSocket', 'V').prop_name = 'V'
		self.outputs.new('SvStringsSocket', 'Vertex')
		self.width = 200
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
		self.outputs['Vertex'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceVertexByParameters)

def unregister():
	bpy.utils.unregister_class(SvFaceVertexByParameters)
