import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from numpy import arctan, pi, signbit
from numpy.linalg import norm
import math

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

def collinear(v1, v2, tol):
	ang = angle_between(v1, v2)
	if math.isnan(ang) or math.isinf(ang):
		raise Exception("Face.IsCollinear - Error: Could not determine the angle between the input faces")
	elif abs(ang) < tol or abs(pi - ang) < tol:
		return True
	return False

replication = [("Default", "Default", "", 1), ("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

def processItem(item):
	faceA, faceB, tol = item
	if not faceA or not isinstance(faceA, topologic.Face):
		raise Exception("Face.IsCoplanar - Error: Face A is not valid")
	if not faceB or not isinstance(faceB, topologic.Face):
		raise Exception("Face.IsCoplanar - Error: Face B is not valid")
	dirA = FaceNormalAtParameters.processItem([faceA, 0.5, 0.5], "XYZ", 3)
	dirB = FaceNormalAtParameters.processItem([faceB, 0.5, 0.5], "XYZ", 3)
	return collinear(dirA, dirB, tol)
		
class SvFaceIsCoplanar(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the input Faces are coplanar, outputs False otherwise.
	"""
	bl_idname = 'SvFaceIsCoplanar'
	bl_label = 'Face.IsCoplanar'
	Tol: FloatProperty(name='Tol', default=0.0001, min=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face A')
		self.inputs.new('SvStringsSocket', 'Face B')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Status')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Status'].sv_set([])
			return
		faceAList = self.inputs['Face A'].sv_get(deepcopy=True)
		faceAList = Replication.flatten(faceAList)
		faceBList = self.inputs['Face B'].sv_get(deepcopy=True)
		faceBList = Replication.flatten(faceBList)
		toleranceList = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)
		toleranceList = Replication.flatten(toleranceList)
		inputs = [faceAList, faceBList, toleranceList]
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
		self.outputs['Status'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceIsCoplanar)

def unregister():
	bpy.utils.unregister_class(SvFaceIsCoplanar)
