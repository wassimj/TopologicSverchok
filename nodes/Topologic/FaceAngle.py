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
	faceA, faceB = item
	if not faceA or not isinstance(faceA, topologic.Face):
		raise Exception("Face.Angle - Error: Face A is not valid")
	if not faceB or not isinstance(faceB, topologic.Face):
		raise Exception("Face.Angle - Error: Face B is not valid")
	dirA = FaceNormalAtParameters.processItem([faceA, 0.5, 0.5], "XYZ", 3)
	dirB = FaceNormalAtParameters.processItem([faceB, 0.5, 0.5], "XYZ", 3)
	return angle_between(dirA, dirB) * 180 / pi # convert to degrees
		
class SvFaceAngle(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the angle, in degrees, of the input Face from another Face
	"""
	bl_idname = 'SvFaceAngle'
	bl_label = 'Face.Angle'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face A')
		self.inputs.new('SvStringsSocket', 'Face B')
		self.outputs.new('SvStringsSocket', 'Angle')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Angle'].sv_set([])
			return
		faceAList = self.inputs['Face A'].sv_get(deepcopy=True)
		faceAList = Replication.flatten(faceAList)
		faceBList = self.inputs['Face B'].sv_get(deepcopy=True)
		faceBList = Replication.flatten(faceBList)
		inputs = [faceAList, faceBList]
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
	bpy.utils.register_class(SvFaceAngle)

def unregister():
	bpy.utils.unregister_class(SvFaceAngle)
