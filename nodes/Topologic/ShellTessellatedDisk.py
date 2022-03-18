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

def faceByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	w = topologic.Wire.ByEdges(edges)
	f = topologic.Face.ByExternalBoundary(w)
	return f

def processItem(item, originLocation):
	origin = item[0]
	radius = item[1]
	sides = item[2]
	rings = item[3]
	dirX = item[4]
	dirY = item[5]
	dirZ = item[6]
	xOffset = 0
	yOffset = 0
	zOffset = 0
	if originLocation == "LowerLeft":
		xOffset = radius
		yOffset = radius
    
	uOffset = float(360)/float(sides)
	vOffset = float(radius)/float(rings)
	faces = []
	for i in range(rings-1):
		r1 = radius - vOffset*i
		r2 = radius - vOffset*(i+1)
		for j in range(sides-1):
			a1 = math.radians(uOffset)*j
			a2 = math.radians(uOffset)*(j+1)
			x1 = math.sin(a1)*r1
			y1 = math.cos(a1)*r1
			z1 = 0
			x2 = math.sin(a1)*r2
			y2 = math.cos(a1)*r2
			z2 = 0
			x3 = math.sin(a2)*r2
			y3 = math.cos(a2)*r2
			z3 = 0
			x4 = math.sin(a2)*r1
			y4 = math.cos(a2)*r1
			z4 = 0
			v1 = topologic.Vertex.ByCoordinates(x1,y1,z1)
			v2 = topologic.Vertex.ByCoordinates(x2,y2,z2)
			v3 = topologic.Vertex.ByCoordinates(x3,y3,z3)
			v4 = topologic.Vertex.ByCoordinates(x4,y4,z4)
			f1 = faceByVertices([v1,v2,v4])
			f2 = faceByVertices([v4,v2,v3])
			faces.append(f1)
			faces.append(f2)
		a1 = math.radians(uOffset)*(sides-1)
		a2 = math.radians(360)
		x1 = math.sin(a1)*r1
		y1 = math.cos(a1)*r1
		z1 = 0
		x2 = math.sin(a1)*r2
		y2 = math.cos(a1)*r2
		z2 = 0
		x3 = math.sin(a2)*r2
		y3 = math.cos(a2)*r2
		z3 = 0
		x4 = math.sin(a2)*r1
		y4 = math.cos(a2)*r1
		z4 = 0
		v1 = topologic.Vertex.ByCoordinates(x1,y1,z1)
		v2 = topologic.Vertex.ByCoordinates(x2,y2,z2)
		v3 = topologic.Vertex.ByCoordinates(x3,y3,z3)
		v4 = topologic.Vertex.ByCoordinates(x4,y4,z4)
		f1 = faceByVertices([v1,v2,v4])
		f2 = faceByVertices([v4,v2,v3])
		faces.append(f1)
		faces.append(f2)

	# Special Case: Center triangles
	r = vOffset
	x1 = 0
	y1 = 0
	z1 = 0
	v1 = topologic.Vertex.ByCoordinates(x1,y1,z1)
	for j in range(sides-1):
			a1 = math.radians(uOffset)*j
			a2 = math.radians(uOffset)*(j+1)
			x2 = math.sin(a1)*r
			y2 = math.cos(a1)*r
			z2 = 0
			x3 = math.sin(a2)*r
			y3 = math.cos(a2)*r
			z3 = 0
			v2 = topologic.Vertex.ByCoordinates(x2,y2,z2)
			v3 = topologic.Vertex.ByCoordinates(x3,y3,z3)
			f1 = faceByVertices([v2,v1,v3])
			faces.append(f1)
	a1 = math.radians(uOffset)*(sides-1)
	a2 = math.radians(360)
	x2 = math.sin(a1)*r
	y2 = math.cos(a1)*r
	z2 = 0
	x3 = math.sin(a2)*r
	y3 = math.cos(a2)*r
	z3 = 0
	v2 = topologic.Vertex.ByCoordinates(x2,y2,z2)
	v3 = topologic.Vertex.ByCoordinates(x3,y3,z3)
	f1 = faceByVertices([v2,v1,v3])
	faces.append(f1)

	shell = topologic.Shell.ByFaces(faces)

	x1 = 0
	y1 = 0
	z1 = 0
	x2 = 0 + dirX
	y2 = 0 + dirY
	z2 = 0 + dirZ
	dx = x2 - x1
	dy = y2 - y1
	dz = z2 - z1    
	dist = math.sqrt(dx**2 + dy**2 + dz**2)
	phi = math.degrees(math.atan2(dy, dx)) # Rotation around Y-Axis
	if dist < 0.0001:
		theta = 0
	else:
		theta = math.degrees(math.acos(dz/dist)) # Rotation around Z-Axis
	zeroOrigin = topologic.Vertex.ByCoordinates(0,0,0)
	shell = topologic.TopologyUtility.Rotate(shell, zeroOrigin, 0, 1, 0, theta)
	shell = topologic.TopologyUtility.Rotate(shell, zeroOrigin, 0, 0, 1, phi)
	shell = topologic.TopologyUtility.Translate(shell, origin.X()+xOffset, origin.Y()+yOffset, origin.Z()+zOffset)
	return shell

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

class SvShellTessellatedDisk(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a tessellated Circle (Shell) from the input parameters    
	"""
	bl_idname = 'SvShellTessellatedDisk'
	bl_label = 'Shell.TessellatedDisk'
	Radius: FloatProperty(name="Radius", default=1, min=0.0001, precision=4, update=updateNode)
	Sides: IntProperty(name="Sides", default=32, min=3, max=360, update=updateNode)
	Rings: IntProperty(name="Rings", default=10, min=1, max=360, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	originLocation: EnumProperty(name="originLocation", description="Specify origin location", default="Bottom", items=originLocations, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'Radius'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'Sides'
		self.inputs.new('SvStringsSocket', 'Rings').prop_name = 'Rings'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.outputs.new('SvStringsSocket', 'Shell')

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
		sidesList = self.inputs['Sides'].sv_get(deepcopy=True)[0]
		ringsList = self.inputs['Rings'].sv_get(deepcopy=True)[0]
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)[0]
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)[0]
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)[0]
		matchLengths([originList, radiusList, sidesList, ringsList, dirXList, dirYList, dirZList])
		newInputs = zip(originList, radiusList, sidesList, ringsList, dirXList, dirYList, dirZList)
		outputs = []
		for anInput in newInputs:
			outputs.append(processItem(anInput, self.originLocation))
		self.outputs['Shell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvShellTessellatedDisk)

def unregister():
	bpy.utils.unregister_class(SvShellTessellatedDisk)
