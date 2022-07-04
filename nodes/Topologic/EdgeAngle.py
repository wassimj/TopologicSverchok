import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from numpy import arctan, pi, signbit
from numpy.linalg import norm

import topologic
from . import Replication, EdgeDirection

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
	edgeA, edgeB = item
	if not edgeA or not isinstance(edgeA, topologic.Edge):
		raise Exception("Edge.Angle - Error: Edge A is not valid")
	if not edgeB or not isinstance(edgeB, topologic.Edge):
		raise Exception("Edge.Angle - Error: Edge B is not valid")
	dirA = EdgeDirection.processItem(edgeA, "XYZ", 3)[0]
	dirB = EdgeDirection.processItem(edgeB, "XYZ", 3)[0]
	return angle_between(dirA, dirB) * 180 / pi # convert to degrees
		
class SvEdgeAngle(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the angle, in degrees, of the input Edge from another Edge
	"""
	bl_idname = 'SvEdgeAngle'
	bl_label = 'Edge.Angle'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge A')
		self.inputs.new('SvStringsSocket', 'Edge B')
		self.outputs.new('SvStringsSocket', 'Angle')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Angle'].sv_set([])
			return
		edgeAList = self.inputs['Edge A'].sv_get(deepcopy=True)
		edgeAList = Replication.flatten(edgeAList)
		edgeBList = self.inputs['Edge B'].sv_get(deepcopy=True)
		edgeBList = Replication.flatten(edgeBList)
		inputs = [edgeAList, edgeBList]
		if ((self.Replication) == "Default"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
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
		self.outputs['Angle'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEdgeAngle)

def unregister():
	bpy.utils.unregister_class(SvEdgeAngle)
