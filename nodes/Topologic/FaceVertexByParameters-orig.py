import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

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
def lace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in lace(ar_list[1:]):
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

def processItem(item):
	face = item[0]
	u = item[1]
	v = item[2]
	vertex = topologic.FaceUtility.VertexAtParameters(face, u, v)
	return vertex

lacing = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Lace", "Lace", "", 4)]

class SvFaceVertexByParameters(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Vertex on the input Face at the input UV parameters    
	"""
	bl_idname = 'SvFaceVertexByParameters'
	bl_label = 'Face.VertexByParameters'
	U: FloatProperty(name="U", default=0.5, precision=4, update=updateNode)
	V: FloatProperty(name="V",  default=0.5, precision=4, update=updateNode)
	Lacing: EnumProperty(name="Lacing", description="Lacing", default="Iterate", items=lacing, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'U').prop_name = 'U'
		self.inputs.new('SvStringsSocket', 'V').prop_name = 'V'
		self.outputs.new('SvStringsSocket', 'Vertex')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Lacing",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Vertex'].sv_set([])
			return
		faceList = self.inputs['Face'].sv_get(deepcopy=True)
		faceList = flatten(faceList)
		uList = self.inputs['U'].sv_get(deepcopy=True)
		uList = flatten(uList)
		vList = self.inputs['V'].sv_get(deepcopy=True)
		vList = flatten(vList)
		inputs = []
		if ((self.Lacing) == "Trim"):
			inputs = trim([faceList, uList, vList])
			inputs = transposeList(inputs)
		if ((self.Lacing) == "Iterate"):
			inputs = iterate([faceList, uList, vList])
			inputs = transposeList(inputs)
		if ((self.Lacing) == "Repeat"):
			inputs = repeat([faceList, uList, vList])
			inputs = transposeList(inputs)
		if ((self.Lacing) == "Lace"):
			inputs = list(lace([faceList, uList, vList]))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Vertex'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceVertexByParameters)

def unregister():
	bpy.utils.unregister_class(SvFaceVertexByParameters)
