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
from . import Replication, CellByLoft

def wireByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def processItem(item, originLocation):
	origin, \
	radius, \
	height, \
	uSides, \
	vSides, \
	dirX, \
	dirY, \
	dirZ, \
	tolerance = item
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

	for i in range(uSides):
		angle = math.radians(360/uSides)*i
		x = math.sin(angle)*radius + origin.X() + xOffset
		y = math.cos(angle)*radius + origin.Y() + yOffset
		z = origin.Z() + zOffset
		baseV.append(topologic.Vertex.ByCoordinates(x,y,z))
		topV.append(topologic.Vertex.ByCoordinates(x,y,z+height))

	baseWire = wireByVertices(baseV)
	topologies = []
	for i in range(vSides+1):
		topologies.append(topologic.TopologyUtility.Translate(baseWire, 0, 0, height/float(vSides)*i))
	cyl = CellByLoft.processItem([topologies, tolerance])

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
	return cyl


originLocations = [("Bottom", "Bottom", "", 1),("Center", "Center", "", 2),("LowerLeft", "LowerLeft", "", 3)]
replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvCellCylinder(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cylinder (Cell) from the input parameters    
	"""
	bl_idname = 'SvCellCylinder'
	bl_label = 'Cell.Cylinder'
	Radius: FloatProperty(name="Radius", default=1, min=0.0001, precision=4, update=updateNode)
	Height: FloatProperty(name="Height", default=1, min=0.0001, precision=4, update=updateNode)
	USides: IntProperty(name="U Sides", default=16, min=3, update=updateNode)
	VSides: IntProperty(name="V Sides", default=1, min=1, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	originLocation: EnumProperty(name="originLocation", description="Specify origin location", default="Bottom", items=originLocations, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'Radius'
		self.inputs.new('SvStringsSocket', 'Height').prop_name = 'Height'
		self.inputs.new('SvStringsSocket', 'U Sides').prop_name = 'USides'
		self.inputs.new('SvStringsSocket', 'V Sides').prop_name = 'VSides'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name='Tolerance'
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
			originList = Replication.flatten(originList)
		radiusList = self.inputs['Radius'].sv_get(deepcopy=True)
		heightList = self.inputs['Height'].sv_get(deepcopy=True)
		uSidesList = self.inputs['U Sides'].sv_get(deepcopy=True)
		vSidesList = self.inputs['V Sides'].sv_get(deepcopy=True)
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		radiusList = Replication.flatten(radiusList)
		heightList = Replication.flatten(heightList)
		uSidesList = Replication.flatten(uSidesList)
		vSidesList = Replication.flatten(vSidesList)
		dirXList = Replication.flatten(dirXList)
		dirYList = Replication.flatten(dirYList)
		dirZList = Replication.flatten(dirZList)
		toleranceList = Replication.flatten(toleranceList)
		inputs = [originList, radiusList, heightList, uSidesList, vSidesList, dirXList, dirYList, dirZList, toleranceList]
		if ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
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
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellCylinder)

def unregister():
	bpy.utils.unregister_class(SvCellCylinder)
