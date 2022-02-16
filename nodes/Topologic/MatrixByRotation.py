import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import math
from mathutils import Matrix

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def repeat(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

# From https://stackoverflow.com/questions/34432056/repeat-elements-of-list-between-each-other-until-we-reach-a-certain-length
def onestep(cur,y,base):
    # one step of the iteration
    if cur is not None:
        y.append(cur)
        base.append(cur)
    else:
        y.append(base[0])  # append is simplest, for now
        base = base[1:]+[base[0]]  # rotate
    return base

def iterate(list):
	maxLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		for i in range(len(anItem), maxLength):
			anItem.append(None)
		y=[]
		base=[]
		for cur in anItem:
			base = onestep(cur,y,base)
			# print(base,y)
		returnList.append(y)
	return returnList

def trim(list):
	minLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength < minLength:
			minLength = newLength
	for anItem in list:
		anItem = anItem[:minLength]
		returnList.append(anItem)
	return returnList

# Adapted from https://stackoverflow.com/questions/533905/get-the-cartesian-product-of-a-series-of-lists
def interlace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in interlace(ar_list[1:]):
                yield [a,]+prod

def transposeList(l):
	length = len(l[0])
	returnList = []
	for i in range(length):
		tempRow = []
		for j in range(len(l)):
			tempRow.append(l[j][i])
		returnList.append(tempRow)
	return returnList

def rotateXMatrix(radians):
	""" Return matrix for rotating about the x-axis by 'radians' radians """
	print("radians",radians)
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
		xList = flatten(xList)
		yList = flatten(yList)
		zList = flatten(zList)
		inputs = [xList, yList, zList]
		if ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, self.rotationOrder))
		self.outputs['Matrix'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvMatrixByRotation)

def unregister():
	bpy.utils.unregister_class(SvMatrixByRotation)
