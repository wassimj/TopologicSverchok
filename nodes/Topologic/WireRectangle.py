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

def wireByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def processItem(item, originLocation):
	origin = item[0]
	width = item[1]
	length = item[2]
	dirX = item[3]
	dirY = item[4]
	dirZ = item[5]
	baseV = []
	xOffset = 0
	yOffset = 0
	if originLocation == "LowerLeft":
		xOffset = width*0.5
		yOffset = length*0.5

	vb1 = topologic.Vertex.ByCoordinates(origin.X()-width*0.5+xOffset,origin.Y()-length*0.5+yOffset,origin.Z())
	vb2 = topologic.Vertex.ByCoordinates(origin.X()+width*0.5+xOffset,origin.Y()-length*0.5+yOffset,origin.Z())
	vb3 = topologic.Vertex.ByCoordinates(origin.X()+width*0.5+xOffset,origin.Y()+length*0.5+yOffset,origin.Z())
	vb4 = topologic.Vertex.ByCoordinates(origin.X()-width*0.5+xOffset,origin.Y()+length*0.5+yOffset,origin.Z())

	baseWire = wireByVertices([vb1, vb2, vb3, vb4])
	x1 = origin.X()
	y1 = origin.Y()
	z1 = origin.Z()
	x2 = origin.X() + dirX
	y2 = origin.Y() + dirY
	z2 = origin.Z() + dirZ
	dx = x2 - x1
	dy = y2 - y1
	dz = z2 - z1    
	dist = math.sqrt(dx**2 + dy**2 + dz**2)
	phi = math.degrees(math.atan2(dy, dx)) # Rotation around Y-Axis
	if dist < 0.0001:
		theta = 0
	else:
		theta = math.degrees(math.acos(dz/dist)) # Rotation around Z-Axis
	baseWire = topologic.TopologyUtility.Rotate(baseWire, origin, 0, 1, 0, theta)
	baseWire = topologic.TopologyUtility.Rotate(baseWire, origin, 0, 0, 1, phi)
	return baseWire


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

originLocations = [("Center", "Center", "", 1),("LowerLeft", "LowerLeft", "", 2)]

class SvWireRectangle(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Prism (Cell) from the input cuboid parameters    
	"""
	bl_idname = 'SvWireRectangle'
	bl_label = 'Wire.Rectangle'
	Width: FloatProperty(name="Width", default=1, min=0.0001, precision=4, update=updateNode)
	Length: FloatProperty(name="Length", default=1, min=0.0001, precision=4, update=updateNode)
	Height: FloatProperty(name="Height", default=1, min=0.0001, precision=4, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)

	originLocation: EnumProperty(name="originLocation", description="Specify origin location", default="Center", items=originLocations, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Width').prop_name = 'Width'
		self.inputs.new('SvStringsSocket', 'Length').prop_name = 'Length'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.outputs.new('SvStringsSocket', 'Wire')

	def draw_buttons(self, context, layout):
		layout.prop(self, "originLocation",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not (self.inputs['Origin'].is_linked):
			originList = [topologic.Vertex.ByCoordinates(0,0,0)]
		else:
			originList = self.inputs['Origin'].sv_get(deepcopy=True)
		widthList = self.inputs['Width'].sv_get(deepcopy=True)[0]
		lengthList = self.inputs['Length'].sv_get(deepcopy=True)[0]
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)[0]
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)[0]
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)[0]
		matchLengths([originList, widthList, lengthList, dirXList, dirYList, dirZList])
		newInputs = zip(originList, widthList, lengthList, dirXList, dirYList, dirZList)
		outputs = []
		for anInput in newInputs:
			outputs.append(processItem(anInput, self.originLocation))
		self.outputs['Wire'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvWireRectangle)

def unregister():
	bpy.utils.unregister_class(SvWireRectangle)
