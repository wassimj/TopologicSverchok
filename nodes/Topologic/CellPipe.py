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

def wireByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def processItem(item):
	edge = item[0]
	radius = item[1]
	sides = item[2]
	startOffset = item[3]
	endOffset = item[4]
	endcapA = item[5]
	endcapB = item[6]

	length = topologic.EdgeUtility.Length(edge)
	origin = edge.StartVertex()
	startU = startOffset / length
	endU = 1.0 - (endOffset / length)
	sv = topologic.EdgeUtility.PointAtParameter(edge, startU)
	ev = topologic.EdgeUtility.PointAtParameter(edge, endU)
	new_edge = topologic.Edge.ByStartVertexEndVertex(sv, ev)
	x1 = sv.X()
	y1 = sv.Y()
	z1 = sv.Z()
	x2 = ev.X()
	y2 = ev.Y()
	z2 = ev.Z()
	dx = x2 - x1
	dy = y2 - y1
	dz = z2 - z1
	dist = math.sqrt(dx**2 + dy**2 + dz**2)
	baseV = []
	topV = []

	for i in range(sides):
		angle = math.radians(360/sides)*i
		x = math.sin(angle)*radius + sv.X()
		y = math.cos(angle)*radius + sv.Y()
		z = sv.Z()
		baseV.append(topologic.Vertex.ByCoordinates(x,y,z))
		topV.append(topologic.Vertex.ByCoordinates(x,y,z+dist))

	baseWire = wireByVertices(baseV)
	topWire = wireByVertices(topV)
	wires = [baseWire, topWire]
	cyl = topologic.CellUtility.ByLoft(wires)
	phi = math.degrees(math.atan2(dy, dx)) # Rotation around Y-Axis
	if dist < 0.0001:
		theta = 0
	else:
		theta = math.degrees(math.acos(dz/dist)) # Rotation around Z-Axis
	cyl = topologic.TopologyUtility.Rotate(cyl, sv, 0, 1, 0, theta)
	cyl = topologic.TopologyUtility.Rotate(cyl, sv, 0, 0, 1, phi)
	zzz = topologic.Vertex.ByCoordinates(0,0,0)
	returnList = [cyl]
	if endcapA:
		origin = edge.StartVertex()
		x1 = origin.X()
		y1 = origin.Y()
		z1 = origin.Z()
		x2 = edge.EndVertex().X()
		y2 = edge.EndVertex().Y()
		z2 = edge.EndVertex().Z()
		dx = x2 - x1
		dy = y2 - y1
		dz = z2 - z1    
		dist = math.sqrt(dx**2 + dy**2 + dz**2)
		phi = math.degrees(math.atan2(dy, dx)) # Rotation around Y-Axis
		if dist < 0.0001:
			theta = 0
		else:
			theta = math.degrees(math.acos(dz/dist)) # Rotation around Z-Axis
		endcapA = topologic.Topology.DeepCopy(endcapA)
		endcapA = topologic.TopologyUtility.Rotate(endcapA, zzz, 0, 1, 0, theta)
		endcapA = topologic.TopologyUtility.Rotate(endcapA, zzz, 0, 0, 1, phi + 180)
		endcapA = topologic.TopologyUtility.Translate(endcapA, origin.X(), origin.Y(), origin.Z())
		returnList.append(endcapA)
	if endcapB:
		origin = edge.EndVertex()
		x1 = origin.X()
		y1 = origin.Y()
		z1 = origin.Z()
		x2 = edge.StartVertex().X()
		y2 = edge.StartVertex().Y()
		z2 = edge.StartVertex().Z()
		dx = x2 - x1
		dy = y2 - y1
		dz = z2 - z1    
		dist = math.sqrt(dx**2 + dy**2 + dz**2)
		phi = math.degrees(math.atan2(dy, dx)) # Rotation around Y-Axis
		if dist < 0.0001:
			theta = 0
		else:
			theta = math.degrees(math.acos(dz/dist)) # Rotation around Z-Axis
		endcapB = topologic.Topology.DeepCopy(endcapB)
		endcapB = topologic.TopologyUtility.Rotate(endcapB, zzz, 0, 1, 0, theta)
		endcapB = topologic.TopologyUtility.Rotate(endcapB, zzz, 0, 0, 1, phi + 180)
		endcapB = topologic.TopologyUtility.Translate(endcapB, origin.X(), origin.Y(), origin.Z())
		returnList.append(endcapB)
	return returnList

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvCellPipe(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Pipe (Cell) along the input Edge    
	"""
	bl_idname = 'SvCellPipe'
	bl_label = 'Cell.Pipe'
	Radius: FloatProperty(name="Radius", default=1, min=0.0001, precision=4, update=updateNode)
	StartOffset: FloatProperty(name="StartOffset", default=0, min=0, precision=4, update=updateNode)
	EndOffset: FloatProperty(name="EndOffset", default=0, min=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Sides: IntProperty(name="Sides", default=16, min=3, max=360, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'Radius'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'Sides'
		self.inputs.new('SvStringsSocket', 'Start Offset').prop_name = 'StartOffset'
		self.inputs.new('SvStringsSocket', 'End Offset').prop_name = 'EndOffset'
		self.inputs.new('SvStringsSocket', 'Endcap A')
		self.inputs.new('SvStringsSocket', 'Endcap B')

		self.outputs.new('SvStringsSocket', 'Pipe')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		edgeList = self.inputs['Edge'].sv_get(deepcopy=True)
		radiusList = self.inputs['Radius'].sv_get(deepcopy=True)
		sidesList = self.inputs['Sides'].sv_get(deepcopy=True)
		startOffsetList = self.inputs['Start Offset'].sv_get(deepcopy=True)
		endOffsetList = self.inputs['End Offset'].sv_get(deepcopy=True)

		edgeList = flatten(edgeList)
		radiusList = flatten(radiusList)
		sidesList = flatten(sidesList)
		startOffsetList = flatten(startOffsetList)
		endOffsetList = flatten(endOffsetList)

		if self.inputs['Endcap A'].is_linked:
			endcapAList = self.inputs['Endcap A'].sv_get(deepcopy=True)
			endcapAList = flatten(endcapAList)
		else:
			endcapAList = [None]
		if self.inputs['Endcap B'].is_linked:
			endcapBList = self.inputs['Endcap B'].sv_get(deepcopy=True)
			endcapBList = flatten(endcapBList)
		else:
			endcapBList = [None]
		inputs = [edgeList, radiusList, sidesList, startOffsetList, endOffsetList, endcapAList, endcapBList]
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
		self.outputs['Pipe'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellPipe)

def unregister():
	bpy.utils.unregister_class(SvCellPipe)
