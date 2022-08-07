import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import math
from mathutils import Matrix
from . import Replication

def rotateXMatrix(radians):
	""" Return matrix for rotating about the x-axis by 'radians' radians """
	c = math.cos(radians)
	s = math.sin(radians)
	return Matrix([[1, 0, 0, 0],
            [0, c,-s, 0],
            [0, s, c, 0],
            [0, 0, 0, 1]]).transposed()

def rotateYMatrix(radians):
	""" Return matrix for rotating about the y-axis by 'radians' radians """
    
	c = math.cos(radians)
	s = math.sin(radians)
	return Matrix([[ c, 0, s, 0],
            [ 0, 1, 0, 0],
            [-s, 0, c, 0],
            [ 0, 0, 0, 1]]).transposed()

def rotateZMatrix(radians):
	""" Return matrix for rotating about the z-axis by 'radians' radians """
    
	c = math.cos(radians)
	s = math.sin(radians)
	return Matrix([[c,-s, 0, 0],
            [s, c, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]).transposed()

def matrixMultiply(matA, matB):
	returnMat = []
	for i in range(len(matA)):
		row = []
		for j in range(len(matB[0])):
			row.append(0)
		returnMat.append(row)

	# iterate through rows of matA
	for i in range(len(matA)):
		# iterate through columns of matB
		for j in range(len(matB[0])):
			# iterate through rows of matB
			for k in range(len(matB)):
				returnMat[i][j] += matA[i][k] * matB[k][j]

def processItem(item, order):
	rx, ry, rz = item
	xMat = rotateXMatrix(math.radians(rx))
	yMat = rotateYMatrix(math.radians(ry))
	zMat = rotateZMatrix(math.radians(rz))
	if order == "XYZ":
		return xMat @ yMat @ zMat
	if order == "XZY":
		return xMat @ zMat @ yMat
	if order == "YXZ":
		return yMat @ xMat @ zMat
	if order == "YZX":
		return yMat @ zMat @ xMat
	if order == "ZXY":
		return zMat @ xMat @ yMat
	if order == "ZYX":
		return zMat @ yMat @ xMat

order = [("XYZ", "XYZ", "", 1),("XZY", "XZY", "", 2),("YXZ", "YXZ", "", 3),("YZX", "YZX", "", 4),("ZXY", "ZXY", "", 5), ("ZYX", "ZYX", "", 6)]
replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]
		
class SvMatrixByRotation(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a Matrix based on the input rotation values    
	"""
	bl_idname = 'SvMatrixByRotation'
	bl_label = 'Matrix.ByRotation'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	rotationOrder: EnumProperty(name="Rotation Order", description="Specify Axis Order for Rotations", default="XYZ", items=order, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.inputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.inputs.new('SvStringsSocket', 'Z').prop_name = 'Z'
		self.outputs.new('SvMatrixSocket', 'Matrix')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "rotationOrder",text="")


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		xList = self.inputs['X'].sv_get(deepcopy=True)
		yList = self.inputs['Y'].sv_get(deepcopy=True)
		zList = self.inputs['Z'].sv_get(deepcopy=True)
		xList = Replication.flatten(xList)
		yList = Replication.flatten(yList)
		zList = Replication.flatten(zList)
		inputs = [xList, yList, zList]
		if ((self.Replication) == "Trim"):
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
			outputs.append(processItem(anInput, self.rotationOrder))
		self.outputs['Matrix'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvMatrixByRotation)

def unregister():
	bpy.utils.unregister_class(SvMatrixByRotation)
