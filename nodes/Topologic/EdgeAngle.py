import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

#from numpy.linalg import norm

import topologic
from . import Replication, EdgeDirection
import math

import numpy as np
import numpy.linalg as la
from numpy import pi

def angle_between(v1, v2):
	""" Returns the angle in radians between vectors 'v1' and 'v2'    """
	n_v1=la.norm(v1)
	n_v2=la.norm(v2)
	if (abs(np.log10(n_v1/n_v2)) > 10):
		v1 = v1/n_v1
		v2 = v2/n_v2
	cosang = np.dot(v1, v2)
	sinang = la.norm(np.cross(v1, v2))
	return np.arctan2(sinang, cosang)

# from https://stackoverflow.com/questions/4114921/vector-normalization
def magnitude(v):
	result = math.sqrt(sum(v[i]*v[i] for i in range(len(v))))
	return result

def add(u, v):
	result = [ u[i]+v[i] for i in range(len(u)) ]
	return result

def sub(u, v):
	result = [ u[i]-v[i] for i in range(len(u)) ]
	return result

def dot(u, v):
	result = sum(u[i]*v[i] for i in range(len(u)))
	return result

def normalize(v):
	vmag = magnitude(v)
	result = [ v[i]/vmag  for i in range(len(v)) ]
	return result

# from https://www.statology.org/cross-product-python/
def cross(a, b):
	result = [a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0]]
	return result


replication = [("Default", "Default", "", 1), ("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

def processItem(item):
	edgeA, edgeB, mantissa, bracket = item
	if not isinstance(edgeA, topologic.Edge) or not isinstance(edgeB, topologic.Edge):
		return None
	dirA = EdgeDirection.processItem([edgeA, mantissa])
	dirB = EdgeDirection.processItem([edgeB, mantissa])
	ang = angle_between(dirA, dirB) * 180 / pi # convert to degrees
	if bracket:
		if ang > 90:
			ang = 180 - ang
	return round(ang, mantissa)
		
class SvEdgeAngle(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the angle, in degrees, of the input Edge from another Edge
	"""
	bl_idname = 'SvEdgeAngle'
	bl_label = 'Edge.Angle'
	bl_icon = 'SELECT_DIFFERENCE'

	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Mantissa: IntProperty(name="Mantissa", default=4, min=0, max=8, update=updateNode)
	Bracket: BoolProperty(name="Bracket", description="Bracket the output angle to between 0 and 90", default=False, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge A')
		self.inputs.new('SvStringsSocket', 'Edge B')
		self.outputs.new('SvStringsSocket', 'Angle')
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
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Mantissa")
		split.row().prop(self, "Mantissa",text="")
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Bracket")
		split.row().prop(self, "Bracket",text="")

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
			outputs.append(processItem(anInput+[self.Mantissa]+[self.Bracket]))
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
	bpy.utils.register_class(SvEdgeAngle)

def unregister():
	bpy.utils.unregister_class(SvEdgeAngle)
