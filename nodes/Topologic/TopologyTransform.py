import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def processItem(item):
	topology, matrix = item
	kTranslationX = 0.0
	kTranslationY = 0.0
	kTranslationZ = 0.0
	kRotation11 = 1.0
	kRotation12 = 0.0
	kRotation13 = 0.0
	kRotation21 = 0.0
	kRotation22 = 1.0
	kRotation23 = 0.0
	kRotation31 = 0.0
	kRotation32 = 0.0
	kRotation33 = 1.0

	kTranslationX = matrix[0][3]
	kTranslationY = matrix[1][3]
	kTranslationZ = matrix[2][3]
	kRotation11 = matrix[0][0]
	kRotation12 = matrix[0][1]
	kRotation13 = matrix[0][2]
	kRotation21 = matrix[1][0]
	kRotation22 = matrix[1][1]
	kRotation23 = matrix[1][2]
	kRotation31 = matrix[2][0]
	kRotation32 = matrix[2][1]
	kRotation33 = matrix[2][2]

	return topologic.TopologyUtility.Transform(topology, kTranslationX, kTranslationY, kTranslationZ, kRotation11, kRotation12, kRotation13, kRotation21, kRotation22, kRotation23, kRotation31, kRotation32, kRotation33)

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
		
class SvTopologyTransform(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Transforms the input Topology based on the input trnasformation matrix    
	"""
	bl_idname = 'SvTopologyTransform'
	bl_label = 'Topology.Transform'
	bl_icon = 'SELECT_DIFFERENCE'

	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvMatrixSocket', 'Matrix')
		self.outputs.new('SvStringsSocket', 'Topology')
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
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyTransform)

def unregister():
	bpy.utils.unregister_class(SvTopologyTransform)
