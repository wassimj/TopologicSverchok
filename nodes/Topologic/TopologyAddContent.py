import bpy
from bpy.props import StringProperty, EnumProperty
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

def processItem(item, targetType):
	topology = item[0]
	contents = flatten(item[1])
	print("Input Contents"+str(contents))
	t = 0
	if targetType == "Vertex":
		t = topologic.Vertex.Type()
	elif targetType == "Edge":
		t = topologic.Edge.Type()
	elif targetType == "Wire":
		t = topologic.Wire.Type()
	elif targetType == "Face":
		t = topologic.Face.Type()
	elif targetType == "Shell":
		t = topologic.Shell.Type()
	elif targetType == "Cell":
		t = topologic.Cell.Type()
	elif targetType == "CellComplex":
		t = topologic.CellComplex.Type()
	elif targetType == "Parent Topology":
		t = 0
	print(t)
	returnTopology = topology.AddContents(contents, t)
	testList = []
	_ = returnTopology.Contents(testList)
	print("Contents: " + str(testList))
	return returnTopology

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]
topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7), ("Parent Topology", "Parent Topology", "", 8)]


class SvTopologyAddContent(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Adds the input Topology content to the input Topology. If the type is set to Topology, the content will be added to the input topology. Otherwise, it will be added to the closest sub-topology of the specified type.   
	"""
	bl_idname = 'SvTopologyAddContent'
	bl_label = 'Topology.AddContent'
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	TargetType: EnumProperty(name="Topology Target", description="Specify topology target", default="Parent Topology", items=topologyTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Content')
		self.outputs.new('SvStringsSocket', 'Topology')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "TargetType",text="Add Content To:")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return

		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		contentList = self.inputs['Content'].sv_get(deepcopy=True)
		topologyList = flatten(topologyList)
		if isinstance(contentList[0], list) == False:
			contentList = [contentList]
		inputs = [topologyList, contentList]
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
			outputs.append(processItem(anInput, self.TargetType))
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvTopologyAddContent)

def unregister():
    bpy.utils.unregister_class(SvTopologyAddContent)
