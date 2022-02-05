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
	radiusA = item[1]
	radiusB = item[2]
	sides = item[3]*2 # Sides is double the number of rays
	dirX = item[4]
	dirY = item[5]
	dirZ = item[6]
	baseV = []

	xList = []
	yList = []
	for i in range(sides):
		if i%2 == 0:
			radius = radiusA
		else:
			radius = radiusB
		angle = math.radians(360/sides)*i
		x = math.sin(angle)*radius + origin.X()
		y = math.cos(angle)*radius + origin.Y()
		z = origin.Z()
		xList.append(x)
		yList.append(y)
		baseV.append([x,y])

	if originLocation == "LowerLeft":
		xmin = min(xList)
		ymin = min(yList)
		xOffset = origin.X() - xmin
		yOffset = origin.Y() - ymin
	else:
		xOffset = 0
		yOffset = 0
	tranBase = []
	for coord in baseV:
		tranBase.append(topologic.Vertex.ByCoordinates(coord[0]+xOffset, coord[1]+yOffset, origin.Z()))
	
	baseWire = wireByVertices(tranBase[::-1]) #reversing the list so that the normal points up in Blender
	
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
	phi = math.degrees(math.atan2(dy, dx)) # Rotation around Z-Axis
	if dist < 0.0001:
		theta = 0
	else:
		theta = math.degrees(math.acos(dz/dist)) # Rotation around Y-Axis
	baseWire = topologic.TopologyUtility.Rotate(baseWire, origin, 0, 1, 0, theta)
	baseWire = topologic.TopologyUtility.Rotate(baseWire, origin, 0, 0, 1, phi)
	centroid = baseWire.Centroid()
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

class SvWireStar(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cylinder (Cell) from the input parameters    
	"""
	bl_idname = 'SvWireStar'
	bl_label = 'Wire.Star'
	RadiusA: FloatProperty(name="Radius A", default=1, min=0.0001, precision=4, update=updateNode)
	RadiusB: FloatProperty(name="Radius B", default=0.4, min=0.0001, precision=4, update=updateNode)
	Rays: IntProperty(name="Rays", default=5, min=2, max=360, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	originLocation: EnumProperty(name="originLocation", description="Specify origin location", default="Center", items=originLocations, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Radius A').prop_name = 'RadiusA'
		self.inputs.new('SvStringsSocket', 'Radius B').prop_name = 'RadiusB'
		self.inputs.new('SvStringsSocket', 'Rays').prop_name = 'Rays'
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
		radiusAList = self.inputs['Radius A'].sv_get(deepcopy=True)[0]
		radiusBList = self.inputs['Radius B'].sv_get(deepcopy=True)[0]
		raysList = self.inputs['Rays'].sv_get(deepcopy=True)[0]
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)[0]
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)[0]
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)[0]
		matchLengths([originList, radiusAList, radiusBList, raysList, dirXList, dirYList, dirZList])
		newInputs = zip(originList, radiusAList, radiusBList, raysList, dirXList, dirYList, dirZList)
		outputs = []
		for anInput in newInputs:
			print(anInput)
			outputs.append(processItem(anInput, self.originLocation))
		self.outputs['Wire'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvWireStar)

def unregister():
	bpy.utils.unregister_class(SvWireStar)
