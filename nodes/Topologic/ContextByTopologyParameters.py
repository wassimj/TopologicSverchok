import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

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

def processItem(item):
	topology = item[0]
	u = item[1]
	v = item[2]
	w = item[3]
	context = None
	try:
		context = topologic.Context.ByTopologyParameters(topology, u, v, w)
	except:
		context = None
	return context

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvContextByTopologyParameters(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Context from the input Topology and parameters   
	"""
	bl_idname = 'SvContextByTopologyParameters'
	bl_label = 'Context.ByTopologyParameters'
	U: FloatProperty(name="U", default=0, precision=4, update=updateNode)
	V: FloatProperty(name="V",  default=0, precision=4, update=updateNode)
	W: FloatProperty(name="W",  default=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		#self.inputs[0].label = 'Auto'
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'U').prop_name = 'U'
		self.inputs.new('SvStringsSocket', 'V').prop_name = 'V'
		self.inputs.new('SvStringsSocket', 'W').prop_name = 'W'
		self.outputs.new('SvStringsSocket', 'Context')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.separator()

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		uList = self.inputs['U'].sv_get(deepcopy=True)
		vList = self.inputs['V'].sv_get(deepcopy=True)
		wList = self.inputs['W'].sv_get(deepcopy=True)
		topologyList = flatten(topologyList)
		uList = flatten(uList)
		vList = flatten(vList)
		wList = flatten(wList)
		inputs = [topologyList, uList, vList, wList]
		if ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlacing"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Context'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvContextByTopologyParameters)

def unregister():
    bpy.utils.unregister_class(SvContextByTopologyParameters)
