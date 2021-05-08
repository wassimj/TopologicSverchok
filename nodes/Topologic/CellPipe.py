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
import cppyy
import math

def classByType(argument):
	switcher = {
		1: Vertex,
		2: Edge,
		4: Wire,
		8: Face,
		16: Shell,
		32: Cell,
		64: CellComplex,
		128: Cluster }
	return switcher.get(argument, Topology)

def fixTopologyClass(topology):
  topology.__class__ = classByType(topology.GetType())
  return topology

def wireByVertices(vList):
	edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	for i in range(len(vList)-1):
		edges.push_back(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.push_back(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def processItem(item):
	edge = item[0]
	radius = item[1]
	sides = item[2]
	startOffset = item[3]
	endOffset = item[4]
	endcapA = item[5]
	endcapB = item[6]

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

	baseV = []
	topV = []
	for i in range(sides):
		angle = math.radians(360/sides)*i
		x = math.sin(angle)*radius + origin.X()
		y = math.cos(angle)*radius + origin.Y()
		z = origin.Z()
		baseV.append(topologic.Vertex.ByCoordinates(x,y,z+startOffset))
		topV.append(topologic.Vertex.ByCoordinates(x,y,z+dist-endOffset))

	baseWire = wireByVertices(baseV)
	topWire = wireByVertices(topV)
	wires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	wires.push_back(baseWire)
	wires.push_back(topWire)
	cyl = topologic.CellUtility.ByLoft(wires)
	phi = math.degrees(math.atan2(dy, dx)) # Rotation around Y-Axis
	if dist < 0.0001:
		theta = 0
	else:
		theta = math.degrees(math.acos(dz/dist)) # Rotation around Z-Axis
	cyl = fixTopologyClass(topologic.TopologyUtility.Rotate(cyl, origin, 0, 1, 0, theta))
	cyl = fixTopologyClass(topologic.TopologyUtility.Rotate(cyl, origin, 0, 0, 1, phi))
	zzz = topologic.Vertex.ByCoordinates(0,0,0)
	returnList = [cyl]
	if endcapA:
		endcapA = topologic.Topology.DeepCopy(endcapA)
		endcapA = topologic.TopologyUtility.Rotate(endcapA, zzz, 0, 1, 0, theta)
		endcapA = topologic.TopologyUtility.Rotate(endcapA, zzz, 0, 0, 1, phi)
		endcapA = fixTopologyClass(topologic.TopologyUtility.Translate(endcapA, origin.X(), origin.Y(), origin.Z()))
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
		endcapB = topologic.TopologyUtility.Rotate(endcapB, zzz, 0, 0, 1, phi)
		endcapB = fixTopologyClass(topologic.TopologyUtility.Translate(endcapB, origin.X(), origin.Y(), origin.Z()))
		returnList.append(endcapB)
	return returnList

def matchLengths(list):
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

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		edgeList = self.inputs['Edge'].sv_get(deepcopy=True)
		radiusList = self.inputs['Radius'].sv_get(deepcopy=True)[0]
		sidesList = self.inputs['Sides'].sv_get(deepcopy=True)[0]
		startOffsetList = self.inputs['Start Offset'].sv_get(deepcopy=True)[0]
		endOffsetList = self.inputs['End Offset'].sv_get(deepcopy=True)[0]
		if self.inputs['Endcap A'].is_linked:
			endcapAList = self.inputs['Endcap A'].sv_get(deepcopy=True)
		else:
			endcapAList = [None]
		if self.inputs['Endcap B'].is_linked:
			endcapBList = self.inputs['Endcap B'].sv_get(deepcopy=True)
		else:
			endcapBList = [None]

		matchLengths([edgeList, radiusList, sidesList, startOffsetList, endOffsetList, endcapAList, endcapBList])
		newInputs = zip(edgeList, radiusList, sidesList, startOffsetList, endOffsetList, endcapAList, endcapBList)
		outputs = []
		for anInput in newInputs:
			outputs.append(processItem(anInput))
		self.outputs['Pipe'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellPipe)

def unregister():
	bpy.utils.unregister_class(SvCellPipe)
