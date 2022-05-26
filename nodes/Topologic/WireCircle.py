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
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import math
from . import Replication, WireByVertices


def processItem(item, originLocation):
	origin, \
	radius, \
	sides, \
	fromAngle, \
	toAngle, \
	close, \
	dirX, \
	dirY, \
	dirZ = item
	baseV = []
	topV = []
	xOffset = 0
	yOffset = 0

	xList = []
	yList = []
	if toAngle < fromAngle:
		toAngle += 360
	elif toAngle == fromAngle:
		raise Exception("Wire.Circle - Error: To angle cannot be equal to the From Angle")
	angleRange = toAngle - fromAngle
	fromAngle = math.radians(fromAngle)
	toAngle = math.radians(toAngle)
	sides = int(math.floor(sides))
	for i in range(sides+1):
		angle = fromAngle + math.radians(angleRange/sides)*i
		x = math.sin(angle)*radius + origin.X()
		y = math.cos(angle)*radius + origin.Y()
		z = origin.Z()
		xList.append(x)
		yList.append(y)
		baseV.append(topologic.Vertex.ByCoordinates(x,y,z))

	baseWire = WireByVertices.processItem([baseV[::-1], close]) #reversing the list so that the normal points up in Blender

	if originLocation == "LowerLeft":
		xmin = min(xList)
		ymin = min(yList)
		baseWire = topologic.TopologyUtility.Translate(baseWire, -xmin, -ymin, 0)
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

originLocations = [("Center", "Center", "", 1),("LowerLeft", "LowerLeft", "", 2)]
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvWireCircle(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a circle (Wire) from the input parameters    
	"""
	bl_idname = 'SvWireCircle'
	bl_label = 'Wire.Circle'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	RadiusProp: FloatProperty(name="Radius", default=1, min=0.0001, precision=4, update=updateNode)
	SidesProp: IntProperty(name="Sides", default=16, min=3, max=360, update=updateNode)
	FromProp: FloatProperty(name="From", description="The start angle of the ellipse", default=0, min=0, max=360, precision=4, update=updateNode)
	ToProp: FloatProperty(name="To", description="The end angle of the ellipse", default=360, min=0, max=360, precision=4, update=updateNode)
	CloseProp: BoolProperty(name="Close", description="Do you wish to close the returned Wire?", default=True, update=updateNode)
	DirXProp: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirYProp: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZProp: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	originLocation: EnumProperty(name="originLocation", description="Specify origin location", default="Center", items=originLocations, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'RadiusProp'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'SidesProp'
		self.inputs.new('SvStringsSocket', 'From').prop_name = 'FromProp'
		self.inputs.new('SvStringsSocket', 'To').prop_name = 'ToProp'
		self.inputs.new('SvStringsSocket', 'Close').prop_name = 'CloseProp'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirXProp'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirYProp'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZProp'
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
			originList = Replication.flatten(originList)
		radiusList = self.inputs['Radius'].sv_get(deepcopy=True)
		radiusList = Replication.flatten(radiusList)
		sidesList = self.inputs['Sides'].sv_get(deepcopy=True)
		sidesList = Replication.flatten(sidesList)
		fromList = self.inputs['From'].sv_get(deepcopy=True)
		fromList = Replication.flatten(fromList)
		toList = self.inputs['To'].sv_get(deepcopy=True)
		toList = Replication.flatten(toList)
		closeList = self.inputs['Close'].sv_get(deepcopy=True)
		closeList = Replication.flatten(closeList)
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)
		dirXList = Replication.flatten(dirXList)
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)
		dirYList = Replication.flatten(dirYList)
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)
		dirZList = Replication.flatten(dirZList)
		inputs = [originList, radiusList, sidesList, fromList, toList, closeList, dirXList, dirYList, dirZList]
		if ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Default" or (self.Replication) == "Iterate"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = Replication.repeat(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(Replication.interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, self.originLocation))
		self.outputs['Wire'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvWireCircle)

def unregister():
	bpy.utils.unregister_class(SvWireCircle)
