import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from numpy import arctan, pi, signbit
from numpy.linalg import norm

import topologic
from . import Replication, FaceNormalAtParameters

def angle_between(v1, v2):
	u1 = v1 / norm(v1)
	u2 = v2 / norm(v2)
	y = u1 - u2
	x = u1 + u2
	a0 = 2 * arctan(norm(y) / norm(x))
	if (not signbit(a0)) or signbit(pi - a0):
		return a0
	elif signbit(a0):
		return 0
	else:
		return pi

replication = [("Default", "Default", "", 1), ("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

def processItem(item):
	faceA, faceB, mantissa = item
	if not faceA or not isinstance(faceA, topologic.Face):
		raise Exception("Face.Angle - Error: Face A is not valid")
	if not faceB or not isinstance(faceB, topologic.Face):
		raise Exception("Face.Angle - Error: Face B is not valid")
	dirA = FaceNormalAtParameters.processItem([faceA, 0.5, 0.5], "XYZ", 3)
	dirB = FaceNormalAtParameters.processItem([faceB, 0.5, 0.5], "XYZ", 3)
	return round((angle_between(dirA, dirB) * 180 / pi), mantissa) # convert to degrees
		
class SvFaceAngle(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the angle, in degrees, of the input Face from another Face
	"""
	bl_idname = 'SvFaceAngle'
	bl_label = 'Face.Angle'
	bl_icon = 'SELECT_DIFFERENCE'

	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Mantissa: IntProperty(name="Mantissa", default=4, min=0, max=8, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face A')
		self.inputs.new('SvStringsSocket', 'Face B')
		self.outputs.new('SvStringsSocket', 'Angle')
		self.width = 175
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Replication")
		split.row().prop(self, "Replication",text="")
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Mantissa")
		split.row().prop(self, "Mantissa",text="")

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
			outputs.append(processItem(anInput+[self.Mantissa]))
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
		self.outputs['Angle'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceAngle)

def unregister():
	bpy.utils.unregister_class(SvFaceAngle)
