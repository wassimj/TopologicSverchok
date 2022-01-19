import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty
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
	sv = item[0]
	ev = item[1]
	tranDict = item[2]
	tol = item[3]
	edge = None
	print("Transfer Dictionary", tranDict)
	if topologic.Topology.IsSame(sv, ev):
		return None
	if topologic.VertexUtility.Distance(sv, ev) < tol:
		return None
	try:
		edge = topologic.Edge.ByStartVertexEndVertex(sv, ev, tranDict)
	except:
		edge = None
	return edge

lacing = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Lace", "Lace", "", 4)]

class SvEdgeByStartVertexEndVertex(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates an Edge from the input Vertices
	"""
	bl_idname = 'SvEdgeByStartVertexEndVertex'
	bl_label = 'Edge.ByStartVertexEndVertex'
	startVertex: StringProperty(name="StartVertex", update=updateNode)
	endVertex: StringProperty(name="EndVertex", update=updateNode)
	TransferDictionary: BoolProperty(name="Transfer Dictionary", default=False, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)
	Lacing: EnumProperty(name="Lacing", description="Lacing", default="Iterate", items=lacing, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'StartVertex')
		self.inputs.new('SvStringsSocket', 'EndVertex')
		self.inputs.new('SvStringsSocket', 'Transfer Dictionary').prop_name = 'TransferDictionary'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Edge')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Lacing",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Edge'].sv_set([])
			return
		svList = self.inputs['StartVertex'].sv_get(deepcopy=True)
		evList = self.inputs['EndVertex'].sv_get(deepcopy=True)
		tranDictList = self.inputs['Transfer Dictionary'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		svList = flatten(svList)
		evList = flatten(evList)
		tranDictList = flatten(tranDictList)
		toleranceList = flatten(toleranceList)
		inputs = [svList, evList, tranDictList, toleranceList]
		if ((self.Lacing) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Lacing) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Lacing) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Lacing) == "Lace"):
			inputs = list(lace(inputs))
		outputs = []
		for anInput in inputs:
			anOutput = processItem(anInput)
			if anOutput:
				outputs.append(anOutput)
		self.outputs['Edge'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvEdgeByStartVertexEndVertex)

def unregister():
    bpy.utils.unregister_class(SvEdgeByStartVertexEndVertex)
