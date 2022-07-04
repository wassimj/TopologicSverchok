import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from mathutils import Vector

from . import Replication

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

def update_sockets(self, context):
	# hide all input sockets
	self.inputs['X'].hide_safe = True
	self.inputs['Y'].hide_safe = True
	self.inputs['Z'].hide_safe = True
	self.inputs['Direction'].hide_safe = True
	self.inputs['Distance'].hide_safe = True

	if self.inputMode == "XYZ":
		self.inputs['X'].hide_safe = False
		self.inputs['Y'].hide_safe = False
		self.inputs['Z'].hide_safe = False
	else:
		self.inputs['Direction'].hide_safe = False
		self.inputs['Distance'].hide_safe = False
	updateNode(self, context)

def processItem(item):
	topology = item[0]
	x = item[1]
	y = item[2]
	z = item[3]
	return topologic.TopologyUtility.Translate(topology, x, y, z)

def processDirectionDistance(item):
	topology = item[0]
	direction = item[1]
	distance = item[2]
	print("Direction", direction)
	dir_vec = Vector((direction[0], direction[1], direction[2]))
	dir_vec.normalize()
	offset = dir_vec*distance
	return processItem([topology, offset[0], offset[1], offset[2]])

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
input_items = [("XYZ", "XYZ", "", 1),("Direction/Distance", "Direction/Distance", "", 2)]

class SvTopologyTranslate(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Translates the input Topology based on the input X,Y,Z translation values    
	"""
	bl_idname = 'SvTopologyTranslate'
	bl_label = 'Topology.Translate'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=0, precision=4, update=updateNode)
	Distance: FloatProperty(name="Distance",  default=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	inputMode : EnumProperty(name='Input Mode', description='The input component format of the data', items=input_items, default="XYZ", update=update_sockets)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.inputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.inputs.new('SvStringsSocket', 'Z').prop_name = 'Z'
		self.inputs.new('SvStringsSocket', 'Direction')
		self.inputs.new('SvStringsSocket', 'Distance').prop_name = 'Distance'
		self.outputs.new('SvStringsSocket', 'Topology')
		update_sockets(self, context)

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "inputMode", expand=False, text="")


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		topologyList = flatten(topologyList)
		if self.inputMode == "XYZ":
			xList = self.inputs['X'].sv_get(deepcopy=True)
			yList = self.inputs['Y'].sv_get(deepcopy=True)
			zList = self.inputs['Z'].sv_get(deepcopy=True)
			xList = flatten(xList)
			yList = flatten(yList)
			zList = flatten(zList)
			inputs = [topologyList, xList, yList, zList]
			if ((self.Replication) == "Trim"):
				inputs = trim(inputs)
				inputs = transposeList(inputs)
			elif (((self.Replication) == "Iterate")  or ((self.Replication) == "Default")):
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
		else:
			directionList = self.inputs['Direction'].sv_get(deepcopy=True)
			#directionList = flatten(directionList)
			distanceList = self.inputs['Distance'].sv_get(deepcopy=True)
			distanceList = flatten(distanceList)
			inputs = [topologyList, directionList, distanceList]
			if ((self.Replication) == "Trim"):
				inputs = trim(inputs)
				inputs = transposeList(inputs)
			elif (((self.Replication) == "Iterate")  or ((self.Replication) == "Default")):
				inputs = iterate(inputs)
				inputs = transposeList(inputs)
			elif ((self.Replication) == "Repeat"):
				inputs = repeat(inputs)
				inputs = transposeList(inputs)
			elif ((self.Replication) == "Interlace"):
				inputs = list(interlace(inputs))
			outputs = []
			for anInput in inputs:
				outputs.append(processDirectionDistance(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyTranslate)

def unregister():
	bpy.utils.unregister_class(SvTopologyTranslate)
