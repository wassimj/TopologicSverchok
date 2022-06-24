#This code is contributed by Neelam Yadav 
import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import time
from collections import defaultdict
from . import DictionarySetValueAtKey
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

def vertexInList(vertex, vertexList):
	if vertex and vertexList:
		if isinstance(vertex, topologic.Vertex) and isinstance(vertexList, list):
			for i in range(len(vertexList)):
				if vertexList[i]:
					if isinstance(vertexList[i], topologic.Vertex):
						if topologic.Topology.IsSame(vertex, vertexList[i]):
							return True
	return False

def getChildren(vertex, parent, graph, masterVertexList):
	children = []
	adjVertices = []
	if vertex:
		_ = topologic.Graph.AdjacentVertices(graph, vertex, adjVertices)
	if parent == None:
		return adjVertices
	else:
		for aVertex in adjVertices:
			if (not vertexInList(aVertex, [parent])) and (not vertexInList(aVertex, masterVertexList)):
				children.append(aVertex)
	return children

def buildTree(vertex, parent, graph, masterVertexList, masterEdgeList, level):
	if not vertexInList(vertex, masterVertexList):
		masterVertexList.append(vertex)
	if parent == None:
		parent = vertex
	children = getChildren(vertex, parent, graph, masterVertexList)
	width = 1
	for aVertex in children:
		v = buildTree(aVertex, vertex, graph, masterVertexList, masterEdgeList, level+1)
		d = v.GetDictionary()
		w = d.ValueAtKey("TOPOLOGIC_width").IntValue()
		width = width + w
		if v:
			vertex = vertex.AddContents([v], 0)
	top_d = vertex.GetDictionary()
	top_d = DictionarySetValueAtKey.processItem(top_d, "TOPOLOGIC_width", width)
	top_d = DictionarySetValueAtKey.processItem(top_d, "TOPOLOGIC_depth", level)
	vertex.SetDictionary(top_d)
	return vertex

def buildGraph(vertex, parent, xSpacing, ySpacing, xStart, vertexMasterList, edgeMasterList):
	d = vertex.GetDictionary()
	width = d.ValueAtKey("TOPOLOGIC_width").IntValue()
	depth = d.ValueAtKey("TOPOLOGIC_depth").IntValue()
	
	xLoc = xStart + 0.5*(width-1)*xSpacing
	yLoc = depth*ySpacing
	newVertex = topologic.Vertex.ByCoordinates(xLoc, yLoc, 0)
	newVertex.SetDictionary(vertex.GetDictionary())
	vertexMasterList.append(newVertex)
	if parent:
		e = topologic.Edge.ByStartVertexEndVertex(parent, newVertex)
		edgeMasterList.append(e)
	children = []
	_ = vertex.Contents(children)
	for aChild in children:
		d = aChild.GetDictionary()
		childWidth = d.ValueAtKey("TOPOLOGIC_width").IntValue()
		vertexMasterList, edgeMasterList = buildGraph(aChild, newVertex, xSpacing, ySpacing, xStart, vertexMasterList, edgeMasterList)
		xStart = xStart + childWidth*xSpacing
	return [vertexMasterList, edgeMasterList]

def processItem(item):
	graph, rootVertex, xSpacing, ySpacing = item
	v = None
	if graph != None and rootVertex != None:
		v = buildTree(rootVertex, None, graph, [], 0)
	else:
		return None
	d = v.GetDictionary()
	width = d.ValueAtKey("TOPOLOGIC_width").IntValue()
	xStart = -width*xSpacing
	vList, eList = buildGraph(v, None, xSpacing, ySpacing, xStart, [], [])
	return topologic.Graph.ByVerticesEdges(vList, eList)


replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvGraphTree(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a Tree representation of the input Graph starting from the input Vertex
	"""
	bl_idname = 'SvGraphTree'
	bl_label = 'Graph.Tree'
	XSpacing: FloatProperty(name='X Spacing', default=1, precision=4, update=updateNode)
	YSpacing: FloatProperty(name='Y Spacing', default=1, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Root Vertex')
		self.inputs.new('SvStringsSocket', 'X Spacing').prop_name='XSpacing'
		self.inputs.new('SvStringsSocket', 'Y Spacing').prop_name='YSpacing'
		self.outputs.new('SvStringsSocket', 'Tree')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		graphList = self.inputs['Graph'].sv_get(deepcopy=True)
		graphList = flatten(graphList)
		rootVertexList = self.inputs['Root Vertex'].sv_get(deepcopy=True)
		rootVertexList = flatten(rootVertexList)
		xSpacingList = self.inputs['X Spacing'].sv_get(deepcopy=True)
		xSpacingList = flatten(xSpacingList)
		ySpacingList = self.inputs['Y Spacing'].sv_get(deepcopy=True)
		ySpacingList = flatten(ySpacingList)
		inputs = [graphList, rootVertexList, xSpacingList, ySpacingList]
		outputs = []
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
			outputs.append(processItem(anInput))
		self.outputs['Tree'].sv_set(outputs)
		end = time.time()
		print("Graph.Tree Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphTree)

def unregister():
    bpy.utils.unregister_class(SvGraphTree)
