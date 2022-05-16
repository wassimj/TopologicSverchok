import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import math

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

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

def unitizeVector(vector):
	mag = 0
	for value in vector:
		mag += value ** 2
	mag = mag ** 0.5
	unitVector = []
	for i in range(len(vector)):
		unitVector.append(vector[i] / mag)
	return unitVector

def processItem(item):
	face, direction, asVertex, tol = item

	faceNormal = topologic.FaceUtility.NormalAtParameters(face,0.5, 0.5)
	faceCenter = topologic.FaceUtility.VertexAtParameters(face,0.5,0.5)
	cList = [faceCenter.X(), faceCenter.Y(), faceCenter.Z()]
	try:
		vList = [direction.X(), direction.Y(), direction.Z()]
	except:
		try:
			vList = [direction[0], direction[1], direction[2]]
		except:
			raise Exception("Face.FacingToward - Error: Could not get the vector from the input direction")
	if asVertex:
		dV = [vList[0]-cList[0], vList[1]-cList[1], vList[2]-cList[2]]
	else:
		dV = vList
	uV = unitizeVector(dV)
	dot = sum([i*j for (i, j) in zip(uV, faceNormal)])
	ang = math.degrees(math.acos(dot))
	if dot < tol:
		return [False, ang]
	return [True, ang]

class SvFaceFacingToward(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the input Face is facing toward the input Vertex. Outputs False otherwise.  
	"""
	bl_idname = 'SvFaceFacingToward'
	bl_label = 'Face.FacingToward'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	AsVertexProp: BoolProperty(name="As Vertex", default=True, update=updateNode)
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'Direction')
		self.inputs.new('SvStringsSocket', 'AsVertex').prop_name = 'AsVertexProp'
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Status')
		self.outputs.new('SvStringsSocket', 'Angle')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Status'].sv_set([])
			self.outputs['Angle'].sv_set([])
			return
		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		directionList = self.inputs['Direction'].sv_get(deepcopy=False)
		asVertexList = self.inputs['AsVertex'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tol'].sv_get(deepcopy=True)

		faceList = flatten(faceList)
		directionList = flatten(directionList)
		asVertexList = flatten(asVertexList)
		toleranceList = flatten(toleranceList)
		inputs = [faceList, directionList, asVertexList, toleranceList]
		if ((self.Replication) == "Default"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Trim"):
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
		statuses = []
		angles = []
		for anInput in inputs:
			output = processItem(anInput)
			statuses.append(output[0])
			angles.append(output[1])
		self.outputs['Status'].sv_set(statuses)
		self.outputs['Angle'].sv_set(angles)

def register():
	bpy.utils.register_class(SvFaceFacingToward)

def unregister():
	bpy.utils.unregister_class(SvFaceFacingToward)
