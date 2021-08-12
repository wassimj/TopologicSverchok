import bpy
from bpy.props import EnumProperty, FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

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

def getColor(ratio):
	r = 0.0
	g = 0.0
	b = 0.0

	finalRatio = ratio;
	if (finalRatio < 0.0):
		finalRatio = 0.0
	elif(finalRatio > 1.0):
		finalRatio = 1.0

	if (finalRatio >= 0.0 and finalRatio <= 0.25):
		r = 0.0
		g = 4.0 * finalRatio
		b = 1.0
	elif (finalRatio > 0.25 and finalRatio <= 0.5):
		r = 0.0
		g = 1.0
		b = 1.0 - 4.0 * (finalRatio - 0.25)
	elif (finalRatio > 0.5 and finalRatio <= 0.75):
		r = 4.0*(finalRatio - 0.5);
		g = 1.0
		b = 0.0
	else:
		r = 1.0
		g = 1.0 - 4.0 * (finalRatio - 0.75)
		b = 0.0

	rcom =  (max(min(r, 1.0), 0.0))
	gcom =  (max(min(g, 1.0), 0.0))
	bcom =  (max(min(b, 1.0), 0.0))

	return [rcom,gcom,bcom]

def processItem(item):
	value = item[0]
	minValue = item[1]
	maxValue = item[2]
	alpha = item[3]
	useAlpha = item[4]
	color = None
	if minValue > maxValue:
		temp = minValue;
		maxValue = minValue
		maxValue = temp

	val = value
	val = max(min(val,maxValue), minValue) # bracket value to the min and max values
	if (maxValue - minValue) != 0:
		val = (val - minValue)/(maxValue - minValue)
	else:
		val = 0
	rgbList = getColor(val)
	if useAlpha:
		rgbList.append(alpha)
	return tuple(rgbList)

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvColorByValueInRange(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a color from the input value within the input range   
	"""
	bl_idname = 'SvColorByValueInRange'
	bl_label = 'Color.ByValueInRange'
	Value: FloatProperty(name="Value", default=0, precision=4, update=updateNode)
	MinValue: FloatProperty(name="Min Value",  default=0, precision=4, update=updateNode)
	MaxValue: FloatProperty(name="Max Value",  default=1, precision=4, update=updateNode)
	Alpha: FloatProperty(name="Alpha",  default=1, min=0, max=1, precision=4, update=updateNode)
	UseAlpha: BoolProperty(name="Use Alpha", default=False, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		#self.inputs[0].label = 'Auto'
		self.inputs.new('SvStringsSocket', 'Value').prop_name = 'Value'
		self.inputs.new('SvStringsSocket', 'Min Value').prop_name = 'MinValue'
		self.inputs.new('SvStringsSocket', 'Max Value').prop_name = 'MaxValue'
		self.inputs.new('SvStringsSocket', 'Alpha').prop_name = 'Alpha'
		self.inputs.new('SvStringsSocket', 'Use Alpha').prop_name = 'UseAlpha'
		self.outputs.new('SvStringsSocket', 'Color')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		valueList = self.inputs['Value'].sv_get(deepcopy=True)
		minValueList = self.inputs['Min Value'].sv_get(deepcopy=True)
		maxValueList = self.inputs['Max Value'].sv_get(deepcopy=True)
		alphaList = self.inputs['Alpha'].sv_get(deepcopy=True)
		useAlphaList = self.inputs['Use Alpha'].sv_get(deepcopy=True)
		valueList = flatten(valueList)
		minValueList = flatten(minValueList)
		maxValueList = flatten(maxValueList)
		alphaList = flatten(alphaList)
		useAlphaList = flatten(useAlphaList)
		inputs = [valueList, minValueList, maxValueList, alphaList, useAlphaList]
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
			outputs.append(processItem(anInput))
		self.outputs['Color'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvColorByValueInRange)

def unregister():
    bpy.utils.unregister_class(SvColorByValueInRange)
