import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

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
	origin = item[1]
	x = item[2]
	y = item[3]
	z = item[4]
	newTopology = None
	try:
		newTopology = topologic.TopologyUtility.Scale(topology, origin, x, y, z)
	except:
		print("ERROR: (Topologic>TopologyUtility.Rotate) operation failed.")
		newTopology = None
	return newTopology

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvTopologyScale(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Scales the input Topology based on the input origin, and X, Y, Z scale factors    
	"""
	bl_idname = 'SvTopologyScale'
	bl_label = 'Topology.Scale'
	XFactor: FloatProperty(name="XFactor", default=1, precision=4, update=updateNode)
	YFactor: FloatProperty(name="YFactor",  default=1, precision=4, update=updateNode)
	ZFactor: FloatProperty(name="ZFactor",  default=1, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'XFactor').prop_name = 'XFactor'
		self.inputs.new('SvStringsSocket', 'YFactor').prop_name = 'YFactor'
		self.inputs.new('SvStringsSocket', 'ZFactor').prop_name = 'ZFactor'
		self.outputs.new('SvStringsSocket', 'Topology')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.separator()

	def process(self):
		originList = []
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		if (self.inputs['Origin'].is_linked):
			originList = self.inputs['Origin'].sv_get(deepcopy=True)
		else:
			for aTopology in topologyList:
				originList.append(aTopology.CenterOfMass())
		xList = self.inputs['XFactor'].sv_get(deepcopy=True)
		yList = self.inputs['YFactor'].sv_get(deepcopy=True)
		zList = self.inputs['ZFactor'].sv_get(deepcopy=True)
		xList = flatten(xList)
		yList = flatten(yList)
		zList = flatten(zList)
		inputs = [topologyList, originList, xList, yList, zList]
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
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyScale)

def unregister():
	bpy.utils.unregister_class(SvTopologyScale)
