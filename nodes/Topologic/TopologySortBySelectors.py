import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import time

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

def topologyContains(topology, vertex, tol):
	contains = False
	if topology.Type() == topologic.Vertex.Type():
		try:
			contains = (topologic.VertexUtility.Distance(vertex, topology) <= tol)
		except:
			contains = False
		return contains
	elif topology.Type() == topologic.Edge.Type():
		try:
			contains = (topologic.VertexUtility.Distance(vertex, topology) <= tol)
		except:
			contains = False
		return contains
	elif topology.Type() == topologic.Wire.Type():
		edges = []
		_ = topology.Edges(None, edges)
		for anEdge in edges:
			try:
				contains = (topologic.VertexUtility.Distance(vertex, anEdge) <= tol)
			except:
				contains = False
			if contains:
				return True
		return False
	elif topology.Type() == topologic.Face.Type():
		return topologic.FaceUtility.IsInside(topology, vertex, tol)
	elif topology.Type() == topologic.Shell.Type():
		faces = []
		_ = topology.Faces(None, faces)
		for aFace in faces:
			if (topologic.FaceUtility.Contains(aFace, vertex, tol) == 0):
				return True
		return False
	elif topology.Type() == topologic.Cell.Type():
		return (topologic.CellUtility.Contains(topology, vertex, tol) == 0)
	elif topology.Type() == topologic.CellComplex.Type():
		cells = []
		_ = topology.Cells(None, cells)
		for aCell in cells:
			if (topologic.CellUtility.Contains(aCell, vertex, tol) == 0):
				return True
		return False
	return False

def processItem(item, tol):
	selectors, topologies, exclusive = item
	usedTopologies = []
	sortedTopologies = []
	unsortedTopologies = []
	for i in range(len(topologies)):
		usedTopologies.append(0)
	
	for i in range(len(selectors)):
		found = False
		for j in range(len(topologies)):
			if usedTopologies[j] == 0:
				if topologyContains(topologies[j], selectors[i], tol):
					sortedTopologies.append(topologies[j])
					if exclusive == True:
						usedTopologies[j] = 1
					found = True
					break
		if found == False:
			sortedTopologies.append(None)
	for i in range(len(usedTopologies)):
		if usedTopologies[i] == 0:
			unsortedTopologies.append(topologies[i])
	return [sortedTopologies, unsortedTopologies]

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvTopologySortBySelectors(bpy.types.Node, SverchCustomTreeNode):

	"""
	Triggers: Topologic
	Tooltip: Sorts the source Topologies based on the location of the input selectors
	"""
	bl_idname = 'SvTopologySortBySelectors'
	bl_label = 'Topology.SortBySelectors'
	Exclusive: BoolProperty(name="Exclusive", default=True, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Selectors')
		self.inputs.new('SvStringsSocket', 'Topologies')
		self.inputs.new('SvStringsSocket', 'Exclusive').prop_name = 'Exclusive'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Sorted Topologies')
		self.outputs.new('SvStringsSocket', 'Unsorted Topologies')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topologies'].sv_set([])
			return
		selectors = self.inputs['Selectors'].sv_get(deepcopy=False)
		topologies = self.inputs['Topologies'].sv_get(deepcopy=False)
		exclusiveList = self.inputs['Exclusive'].sv_get(deepcopy=True)
		tolerance = self.inputs['Tolerance'].sv_get(deepcopy=False)[0][0]
		selectors = flatten(selectors)
		topologies = flatten(topologies)
		exclusiveList = flatten(exclusiveList)
		inputs = [[selectors], [topologies], exclusiveList]
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
		sortedTopologies = []
		unsortedTopologies = []
		for anInput in inputs:
			output = processItem(anInput, tolerance)
			sortedTopologies.append(output[0])
			unsortedTopologies.append(output[1])
		self.outputs['Sorted Topologies'].sv_set(sortedTopologies)
		self.outputs['Unsorted Topologies'].sv_set(unsortedTopologies)
		end = time.time()
		print("Topology.SortBySelectors Operation consumed "+str(round(end - start,2)*1000)+" ms")

def register():
    bpy.utils.register_class(SvTopologySortBySelectors)

def unregister():
    bpy.utils.unregister_class(SvTopologySortBySelectors)
