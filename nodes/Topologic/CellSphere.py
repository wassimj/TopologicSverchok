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
from . import Replication, TopologySpin, WireCircle

def wireByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def processItem(item, originLocation):
	origin, \
	radius, \
	uSides, \
	vSides, \
	dirX, \
	dirY, \
	dirZ, \
	tolerance = item

	c = WireCircle.processItem([origin, radius, vSides, 90, 270, True, 0, 1, 0], "Center")
	c = topologic.Face.ByExternalBoundary(c)
	s = TopologySpin.processItem([c, origin, 0, 0, 1, 360, uSides, tolerance])
	if s.Type() == topologic.CellComplex.Type():
		s = s.ExternalBoundary()
	if s.Type() == topologic.Shell.Type():
		s = topologic.Cell.ByShell(s)
	if originLocation == "Bottom":
		s = topologic.TopologyUtility.Translate(s, 0, 0, radius)
	elif originLocation == "LowerLeft":
		s = topologic.TopologyUtility.Translate(s, radius, radius, radius)
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
	s = topologic.TopologyUtility.Rotate(s, origin, 0, 1, 0, theta)
	s = topologic.TopologyUtility.Rotate(s, origin, 0, 0, 1, phi)
	return s

originLocations = [("Bottom", "Bottom", "", 1),("Center", "Center", "", 2),("LowerLeft", "Lower Left", "", 3)]
replication = [("Default", "Default", "", 1), ("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvCellSphere(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Sphere (Cell) from the input parameters    
	"""
	bl_idname = 'SvCellSphere'
	bl_label = 'Cell.Sphere'
	Radius: FloatProperty(name="Radius", default=1, min=0.0001, precision=4, update=updateNode)
	USides: IntProperty(name="U Sides", default=16, min=3, update=updateNode)
	VSides: IntProperty(name="V Sides", default=8, min=3, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	originLocation: EnumProperty(name="originLocation", description="Specify origin location", default="Center", items=originLocations, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'Radius'
		self.inputs.new('SvStringsSocket', 'U Sides').prop_name = 'USides'
		self.inputs.new('SvStringsSocket', 'V Sides').prop_name = 'VSides'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
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
		uSidesList = self.inputs['U Sides'].sv_get(deepcopy=True)
		vSidesList = self.inputs['V Sides'].sv_get(deepcopy=True)
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		radiusList = Replication.flatten(radiusList)
		uSidesList = Replication.flatten(uSidesList)
		vSidesList = Replication.flatten(vSidesList)
		dirXList = Replication.flatten(dirXList)
		dirYList = Replication.flatten(dirYList)
		dirZList = Replication.flatten(dirZList)
		toleranceList = Replication.flatten(toleranceList)
		inputs = [originList, radiusList, uSidesList, vSidesList, dirXList, dirYList, dirZList, toleranceList]
		if ((self.Replication) == "Default"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Trim"):
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
	bpy.utils.register_class(SvCellSphere)

def unregister():
	bpy.utils.unregister_class(SvCellSphere)
