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
	radius = item[1]
	height = item[2]
	sides = item[3]
	dirX = item[4]
	dirY = item[5]
	dirZ = item[6]
	baseV = []
	topV = []
	xOffset = 0
	yOffset = 0
	zOffset = 0
	if originLocation == "Center":
		zOffset = -height*0.5
	elif originLocation == "LowerLeft":
		xOffset = radius
		yOffset = radius

	for i in range(sides):
		angle = math.radians(360/sides)*i
		x = math.sin(angle)*radius + origin.X() + xOffset
		y = math.cos(angle)*radius + origin.Y() + yOffset
		z = origin.Z() + zOffset
		baseV.append(topologic.Vertex.ByCoordinates(x,y,z))
		topV.append(topologic.Vertex.ByCoordinates(x,y,z+height))

	baseWire = wireByVertices(baseV)
	topWire = wireByVertices(topV)
	wires = [baseWire, topWire]
	cyl = topologic.CellUtility.ByLoft(wires)
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
	cyl = topologic.TopologyUtility.Rotate(cyl, origin, 0, 1, 0, theta)
	cyl = topologic.TopologyUtility.Rotate(cyl, origin, 0, 0, 1, phi)
	return topologic.CellUtility.ByLoft(wires)

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

originLocations = [("Bottom", "Bottom", "", 1),("Center", "Center", "", 2),("LowerLeft", "LowerLeft", "", 3)]

class SvCellCylinder(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cylinder (Cell) from the input parameters    
	"""
	bl_idname = 'SvCellCylinder'
	bl_label = 'Cell.Cylinder'
	Radius: FloatProperty(name="Radius", default=1, min=0.0001, precision=4, update=updateNode)
	Height: FloatProperty(name="Height", default=1, min=0.0001, precision=4, update=updateNode)
	Sides: IntProperty(name="Sides", default=16, min=3, max=360, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	originLocation: EnumProperty(name="originLocation", description="Specify origin location", default="Bottom", items=originLocations, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'Radius'
		self.inputs.new('SvStringsSocket', 'Height').prop_name = 'Height'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'Sides'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.outputs.new('SvStringsSocket', 'Cell')

	def draw_buttons(self, context, layout):
		layout.prop(self, "originLocation",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not (self.inputs['Origin'].is_linked):
			originList = [topologic.Vertex.ByCoordinates(0,0,0)]
		else:
			originList = self.inputs['Origin'].sv_get(deepcopy=True)
		radiusList = self.inputs['Radius'].sv_get(deepcopy=True)[0]
		heightList = self.inputs['Height'].sv_get(deepcopy=True)[0]
		sidesList = self.inputs['Sides'].sv_get(deepcopy=True)[0]
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)[0]
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)[0]
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)[0]
		matchLengths([originList, radiusList, heightList, sidesList, dirXList, dirYList, dirZList])
		newInputs = zip(originList, radiusList, heightList, sidesList, dirXList, dirYList, dirZList)
		outputs = []
		for anInput in newInputs:
			outputs.append(processItem(anInput, self.originLocation))
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellCylinder)

def unregister():
	bpy.utils.unregister_class(SvCellCylinder)
