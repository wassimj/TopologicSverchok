import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary

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


def processItem(input):
	topoA = input[0]
	topoB = input[1]
	vertices = input[2]
	edges = input[3]
	wires = input[4]
	faces = input[5]
	vOutput = []
	eOutput = []
	wOutput = []
	fOutput = []
	if vertices:
		_ = topoA.SharedTopologies(topoB, 1, vOutput)
	if edges:
		_ = topoA.SharedTopologies(topoB, 2, eOutput)
	if wires:
		_ = topoA.SharedTopologies(topoB, 4, wOutput)
	if faces:
		_ = topoA.SharedTopologies(topoB, 8, fOutput)
	return [vOutput, eOutput, wOutput, fOutput]

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvTopologySharedTopologies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Returns the shared topologies of the two input toplogies of a certain type specified by the input type filters
	"""
	bl_idname = 'SvTopologySharedTopologies'
	bl_label = 'Topology.SharedTopologies'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	SharedVertices: BoolProperty(name="Shared Vertices", default=True, update=updateNode)
	SharedEdges: BoolProperty(name="Shared Edges", default=True, update=updateNode)
	SharedWires: BoolProperty(name="Shared Wires", default=True, update=updateNode)
	SharedFaces: BoolProperty(name="Shared Faces", default=True, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology A')
		self.inputs.new('SvStringsSocket', 'Topology B')
		self.inputs.new('SvStringsSocket', 'Vertices').prop_name = 'SharedVertices'
		self.inputs.new('SvStringsSocket', 'Edges').prop_name = 'SharedEdges'
		self.inputs.new('SvStringsSocket', 'Wires').prop_name = 'SharedWires'
		self.inputs.new('SvStringsSocket', 'Faces').prop_name = 'SharedFaces'
		self.outputs.new('SvStringsSocket', 'Vertices')
		self.outputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Wires')
		self.outputs.new('SvStringsSocket', 'Faces')


	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyAList = self.inputs['Topology A'].sv_get(deepcopy=True)
		topologyBList = self.inputs['Topology B'].sv_get(deepcopy=True)
		verticesList = self.inputs['Vertices'].sv_get(deepcopy=True)
		edgesList = self.inputs['Edges'].sv_get(deepcopy=True)
		wiresList = self.inputs['Wires'].sv_get(deepcopy=True)
		facesList = self.inputs['Faces'].sv_get(deepcopy=True)
		topologyAList = flatten(topologyAList)
		topologyBList = flatten(topologyBList)
		verticesList = flatten(verticesList)
		edgesList = flatten(edgesList)
		wiresList = flatten(wiresList)
		facesList = flatten(facesList)
		inputs = [topologyAList, topologyBList, verticesList, edgesList, wiresList, facesList]
		verticesOutputs = []
		edgesOutputs = []
		wiresOutputs = []
		facesOutputs = []
		if ((self.Replication) == "Default"):
			inputs = repeat(inputs)
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
		for anInput in inputs:
			output = processItem(anInput)
			verticesOutputs.append(output[0])
			edgesOutputs.append(output[1])
			wiresOutputs.append(output[2])
			facesOutputs.append(output[3])
		self.outputs['Vertices'].sv_set(verticesOutputs)
		self.outputs['Edges'].sv_set(edgesOutputs)
		self.outputs['Wires'].sv_set(wiresOutputs)
		self.outputs['Faces'].sv_set(facesOutputs)

def register():
	bpy.utils.register_class(SvTopologySharedTopologies)

def unregister():
	bpy.utils.unregister_class(SvTopologySharedTopologies)
