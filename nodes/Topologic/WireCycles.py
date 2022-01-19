# * This file is part of Topologic software library.
# * Copyright(C) 2021, Cardiff University and University College London
# * 
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU Affero General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# * 
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU Affero General Public License for more details.
# * 
# * You should have received a copy of the GNU Affero General Public License
# * along with this program. If not, see <https://www.gnu.org/licenses/>.

import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import math
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

#Based on open source code from: https://stackoverflow.com/questions/12367801/finding-all-cycles-in-undirected-graphs

def vIndex(v, vList, tolerance):
    for i in range(len(vList)):
        if topologic.VertexUtility.Distance(v, vList[i]) < tolerance:
            return i+1
    return None

#  rotate cycle path such that it begins with the smallest node
def rotate_to_smallest(path):
    n = path.index(min(path))
    return path[n:]+path[:n]

def invert(path):
    return rotate_to_smallest(path[::-1])

def isNew(cycles, path):
    return not path in cycles

def visited(node, path):
    return node in path

def findNewCycles(graph, cycles, path, maxVertices):
    if len(path) > maxVertices:
        return
    start_node = path[0]
    next_node= None
    sub = []

    #visit each edge and each node of each edge
    for edge in graph:
        node1, node2 = edge
        if start_node in edge:
                if node1 == start_node:
                    next_node = node2
                else:
                    next_node = node1
                if not visited(next_node, path):
                        # neighbor node not on path yet
                        sub = [next_node]
                        sub.extend(path)
                        # explore extended path
                        findNewCycles(graph, cycles, sub, maxVertices);
                elif len(path) > 2  and next_node == path[-1]:
                        # cycle found
                        p = rotate_to_smallest(path);
                        inv = invert(p)
                        if isNew(cycles, p) and isNew(cycles, inv):
                            cycles.append(p)

def main(graph, cycles, maxVertices):
    returnValue = []
    for edge in graph:
        for node in edge:
            findNewCycles(graph, cycles, [node], maxVertices)
    for cy in cycles:
        row = []
        for node in cy:
            row.append(node)
        returnValue.append(row)
    return returnValue

def processItem(item):
	wire = item[0]
	maxVertices = item[1]
	tolerance = item[2]

	tEdges = []
	_ = wire.Edges(None, tEdges)
	tVertices = []
	_ = wire.Vertices(None, tVertices)
	tVertices = tVertices

	graph = []
	for anEdge in tEdges:
		graph.append([vIndex(anEdge.StartVertex(), tVertices, tolerance), vIndex(anEdge.EndVertex(), tVertices, tolerance)])

	cycles = []
	resultingCycles = main(graph, cycles, maxVertices)

	result = []
	for aRow in resultingCycles:
		row = []
		for anIndex in aRow:
			row.append(tVertices[anIndex-1])
		result.append(row)

	resultWires = []
	for i in range(len(result)):
		c = result[i]
		resultEdges = []
		for j in range(len(c)-1):
			v1 = c[j]
			v2 = c[j+1]
			e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
			resultEdges.append(e)
		e = topologic.Edge.ByStartVertexEndVertex(c[len(c)-1], c[0])
		resultEdges.append(e)
		resultWire = topologic.Wire.ByEdges(resultEdges)
		resultWires.append(resultWire)
	return resultWires

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvWireCycles(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the closed cycles (Wires) with the maximum number of input Vertices found in the inut Wire    
	"""
	bl_idname = 'SvWireCycles'
	bl_label = 'Wire.Cycles'
	MaxVertices: IntProperty(name="Max Vertices", default=16, min=3, max=360, update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.inputs.new('SvStringsSocket', 'MaxVertices').prop_name = 'MaxVertices'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Cycles')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		wireList = self.inputs['Wire'].sv_get(deepcopy=True)
		maxVerticesList = self.inputs['MaxVertices'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		wireList = flatten(wireList)
		maxVerticesList = flatten(maxVerticesList)
		toleranceList = flatten(toleranceList)
		inputs = [wireList, maxVerticesList, toleranceList]
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
		self.outputs['Cycles'].sv_set(outputs)
		end = time.time()
		print("Wire.Cycles Operation consumed "+str(round(end - start,2))+" seconds")


def register():
	bpy.utils.register_class(SvWireCycles)

def unregister():
	bpy.utils.unregister_class(SvWireCycles)
