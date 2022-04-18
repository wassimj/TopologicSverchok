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
from . import Replication
import math

def faceByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	w = topologic.Wire.ByEdges(edges)
	f = topologic.Face.ByExternalBoundary(w)
	return f

def processItemRectangularDomain(item, originLocation):
	origin, llVertex, lrVertex, urVertex, ulVertex, u, v, dirX, dirY, dirZ = item
	e1 = topologic.Edge.ByStartVertexEndVertex(llVertex, lrVertex)
	e2 = topologic.Edge.ByStartVertexEndVertex(lrVertex, urVertex)
	e3 = topologic.Edge.ByStartVertexEndVertex(urVertex, ulVertex)
	e4 = topologic.Edge.ByStartVertexEndVertex(ulVertex, llVertex)
	edges = []
	for i in range(u+1):
		print("I", i)
		v1 = topologic.EdgeUtility.PointAtParameter(e1, float(i)/float(u))
		v2 = topologic.EdgeUtility.PointAtParameter(e3, 1.0 - float(i)/float(u))
		edges.append(topologic.Edge.ByStartVertexEndVertex(v1, v2))
	faces = []
	for i in range(u):
		for j in range(v):
			v1 = topologic.EdgeUtility.PointAtParameter(edges[i], float(j)/float(v))
			v2 = topologic.EdgeUtility.PointAtParameter(edges[i], float(j+1)/float(v))
			v3 = topologic.EdgeUtility.PointAtParameter(edges[i+1], float(j+1)/float(v))
			v4 = topologic.EdgeUtility.PointAtParameter(edges[i+1], float(j)/float(v))
			faces.append(faceByVertices([v1, v2, v4]))
			faces.append(faceByVertices([v4, v2, v3]))
	returnTopology = topologic.Shell.ByFaces(faces)
	if not returnTopology:
		returnTopology = topologic.Cluster.ByTopologies(faces)
	zeroOrigin = returnTopology.CenterOfMass()
	xOffset = 0
	yOffset = 0
	zOffset = 0
	minX = min([llVertex.X(), lrVertex.X(), ulVertex.X(), urVertex.X()])
	maxX = max([llVertex.X(), lrVertex.X(), ulVertex.X(), urVertex.X()])
	minY = min([llVertex.Y(), lrVertex.Y(), ulVertex.Y(), urVertex.Y()])
	maxY = max([llVertex.Y(), lrVertex.Y(), ulVertex.Y(), urVertex.Y()])
	minZ = min([llVertex.Z(), lrVertex.Z(), ulVertex.Z(), urVertex.Z()])
	maxZ = max([llVertex.Z(), lrVertex.Z(), ulVertex.Z(), urVertex.Z()])
	if originLocation == "LowerLeft":
		xOffset = -minX
		yOffset = -minY
		zOffset = -minZ
	elif originLocation == "Bottom":
		xOffset = -(minX + (maxX - minX)*0.5)
		yOffset = -(minY + (maxY - minY)*0.5)
		zOffset = -minZ
	elif originLocation == "Center":
		xOffset = -(minX + (maxX - minX)*0.5)
		yOffset = -(minY + (maxY - minY)*0.5)
		zOffset = -(minZ + (maxZ - minZ)*0.5)
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
	returnTopology = topologic.TopologyUtility.Rotate(returnTopology, zeroOrigin, 0, 1, 0, theta)
	returnTopology = topologic.TopologyUtility.Rotate(returnTopology, zeroOrigin, 0, 0, 1, phi)
	returnTopology = topologic.TopologyUtility.Translate(returnTopology, zeroOrigin.X()+xOffset, zeroOrigin.Y()+yOffset, zeroOrigin.Z()+zOffset)
	return returnTopology

def processItemCircularDomain(item, originLocation):
	origin = item[0]
	radius = item[1]
	sides = item[2]
	rings = item[3]
	A = item[4]
	B = item[5]
	dirX = item[6]
	dirY = item[7]
	dirZ = item[8]
    
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
			z1 = A*x1*x1 + B*y1*y1
			x2 = math.sin(a1)*r2
			y2 = math.cos(a1)*r2
			z2 = A*x2*x2 + B*y2*y2
			x3 = math.sin(a2)*r2
			y3 = math.cos(a2)*r2
			z3 = A*x3*x3 + B*y3*y3
			x4 = math.sin(a2)*r1
			y4 = math.cos(a2)*r1
			z4 = A*x4*x4 + B*y4*y4
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
		z1 = A*x1*x1 + B*y1*y1
		x2 = math.sin(a1)*r2
		y2 = math.cos(a1)*r2
		z2 = A*x2*x2 + B*y2*y2
		x3 = math.sin(a2)*r2
		y3 = math.cos(a2)*r2
		z3 = A*x3*x3 + B*y3*y3
		x4 = math.sin(a2)*r1
		y4 = math.cos(a2)*r1
		z4 = A*x4*x4 + B*y4*y4
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
			z2 = A*x2*x2 + B*y2*y2
			#z2 = 0
			x3 = math.sin(a2)*r
			y3 = math.cos(a2)*r
			z3 = A*x3*x3 + B*y3*y3
			#z3 = 0
			v2 = topologic.Vertex.ByCoordinates(x2,y2,z2)
			v3 = topologic.Vertex.ByCoordinates(x3,y3,z3)
			f1 = faceByVertices([v2,v1,v3])
			faces.append(f1)
	a1 = math.radians(uOffset)*(sides-1)
	a2 = math.radians(360)
	x2 = math.sin(a1)*r
	y2 = math.cos(a1)*r
	z2 = A*x2*x2 + B*y2*y2
	x3 = math.sin(a2)*r
	y3 = math.cos(a2)*r
	z3 = A*x3*x3 + B*y3*y3
	v2 = topologic.Vertex.ByCoordinates(x2,y2,z2)
	v3 = topologic.Vertex.ByCoordinates(x3,y3,z3)
	f1 = faceByVertices([v2,v1,v3])
	faces.append(f1)
	returnTopology = topologic.Shell.ByFaces(faces)
	if not returnTopology:
		returnTopology = topology.Cluster.ByTopologies(faces)
	vertices = []
	_ = returnTopology.Vertices(None, vertices)
	xList = []
	yList = []
	zList = []
	for aVertex in vertices:
		xList.append(aVertex.X())
		yList.append(aVertex.Y())
		zList.append(aVertex.Z())
	minX = min(xList)
	maxX = max(xList)
	minY = min(yList)
	maxY = max(yList)
	minZ = min(zList)
	maxZ = max(zList)
	zeroOrigin = returnTopology.CenterOfMass()
	xOffset = 0
	yOffset = 0
	zOffset = 0
	if originLocation == "LowerLeft":
		xOffset = -minX
		yOffset = -minY
		zOffset = -minZ
	elif originLocation == "Bottom":
		xOffset = -(minX + (maxX - minX)*0.5)
		yOffset = -(minY + (maxY - minY)*0.5)
		zOffset = -minZ
	elif originLocation == "Center":
		xOffset = -(minX + (maxX - minX)*0.5)
		yOffset = -(minY + (maxY - minY)*0.5)
		zOffset = -(minZ + (maxZ - minZ)*0.5)
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
	returnTopology = topologic.TopologyUtility.Rotate(returnTopology, zeroOrigin, 0, 1, 0, theta)
	returnTopology = topologic.TopologyUtility.Rotate(returnTopology, zeroOrigin, 0, 0, 1, phi)
	returnTopology = topologic.TopologyUtility.Translate(returnTopology, origin.X()+xOffset, origin.Y()+yOffset, origin.Z()+zOffset)
	return returnTopology

def update_sockets(self, context):
	# Common sockets should always be visible
	
	# hide all other input sockets
	# Circular
	self.inputs['Radius'].hide_safe = True
	self.inputs['Sides'].hide_safe = True
	self.inputs['Rings'].hide_safe = True
	self.inputs['A'].hide_safe = True
	self.inputs['B'].hide_safe = True
	self.inputs['Origin'].hide_safe = True
	self.inputs['Dir X'].hide_safe = True
	self.inputs['Dir Y'].hide_safe = True
	self.inputs['Dir Z'].hide_safe = True
	# Rectangular
	self.inputs['LL Vertex'].hide_safe = True
	self.inputs['LR Vertex'].hide_safe = True
	self.inputs['UR Vertex'].hide_safe = True
	self.inputs['UL Vertex'].hide_safe = True
	self.inputs['U'].hide_safe = True
	self.inputs['V'].hide_safe = True

	if self.domain == "Circular":
		self.inputs['Radius'].hide_safe = False
		self.inputs['Sides'].hide_safe = False
		self.inputs['Rings'].hide_safe = False
		self.inputs['A'].hide_safe = False
		self.inputs['B'].hide_safe = False
		self.inputs['Origin'].hide_safe = False
		self.inputs['Dir X'].hide_safe = False
		self.inputs['Dir Y'].hide_safe = False
		self.inputs['Dir Z'].hide_safe = False
	else:
		self.inputs['LL Vertex'].hide_safe = False
		self.inputs['LR Vertex'].hide_safe = False
		self.inputs['UR Vertex'].hide_safe = False
		self.inputs['UL Vertex'].hide_safe = False
		self.inputs['U'].hide_safe = False
		self.inputs['V'].hide_safe = False
		self.inputs['Origin'].hide_safe = False
		self.inputs['Dir X'].hide_safe = False
		self.inputs['Dir Y'].hide_safe = False
		self.inputs['Dir Z'].hide_safe = False
	updateNode(self, context)

originLocations = [("Bottom", "Bottom", "", 1),("Center", "Center", "", 2),("LowerLeft", "LowerLeft", "", 3)]
domains = [("Circular", "Circular", "", 1),("Rectangular", "Rectangular", "", 2)]
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvShellHyperbolicParaboloid(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a tessellated Hyperbolic Paraboloid (Shell) from the input parameters    
	"""
	bl_idname = 'SvShellHyperbolicParaboloid'
	bl_label = 'Shell.HyperbolicPraboloid'
	Radius: FloatProperty(name="Radius", default=1, min=0.0001, precision=4, update=updateNode)
	Sides: IntProperty(name="Sides", default=36, min=3, update=updateNode)
	Rings: IntProperty(name="Rings", default=10, min=1, update=updateNode)
	A: FloatProperty(name="A", default=1, precision=4, update=updateNode)
	B: FloatProperty(name="B", default=-1, precision=4, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	U: IntProperty(name="U", default=10, min=1, update=updateNode)
	V: IntProperty(name="V", default=10, min=1, update=updateNode)
	originLocation: EnumProperty(name="originLocation", description="Specify origin location", default="Bottom", items=originLocations, update=updateNode)
	domain : EnumProperty(name='Domain', description='Domain', items=domains, default="Circular", update=update_sockets)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'Radius'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'Sides'
		self.inputs.new('SvStringsSocket', 'Rings').prop_name = 'Rings'
		self.inputs.new('SvStringsSocket', 'A').prop_name = 'A'
		self.inputs.new('SvStringsSocket', 'B').prop_name = 'B'
		self.inputs.new('SvStringsSocket', 'LL Vertex')
		self.inputs.new('SvStringsSocket', 'LR Vertex')
		self.inputs.new('SvStringsSocket', 'UR Vertex')
		self.inputs.new('SvStringsSocket', 'UL Vertex')
		self.inputs.new('SvStringsSocket', 'U').prop_name = 'U'
		self.inputs.new('SvStringsSocket', 'V').prop_name = 'V'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.outputs.new('SvStringsSocket', 'Shell')
		update_sockets(self, context)

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "originLocation",text="")
		layout.prop(self, "domain", expand=False, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not (self.inputs['Origin'].is_linked):
			originList = [topologic.Vertex.ByCoordinates(0,0,0)]
		else:
			originList = self.inputs['Origin'].sv_get(deepcopy=True)
			originList = Replication.flatten(originList)
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)
		dirXList = Replication.flatten(dirXList)
		dirYList = Replication.flatten(dirYList)
		dirZList = Replication.flatten(dirZList)
		# Circular Domain
		if self.domain == "Circular":
			radiusList = self.inputs['Radius'].sv_get(deepcopy=True)
			sidesList = self.inputs['Sides'].sv_get(deepcopy=True)
			ringsList = self.inputs['Rings'].sv_get(deepcopy=True)
			aList = self.inputs['A'].sv_get(deepcopy=True)
			bList = self.inputs['B'].sv_get(deepcopy=True)
			radiusList = Replication.flatten(radiusList)
			sidesList = Replication.flatten(sidesList)
			ringsList = Replication.flatten(ringsList)
			aList = Replication.flatten(aList)
			bList = Replication.flatten(bList)

			inputs = [originList, radiusList, sidesList, ringsList, aList, bList, dirXList, dirYList, dirZList]
			if ((self.Replication) == "Trim"):
				inputs = Replication.trim(inputs)
				inputs = Replication.transposeList(inputs)
			elif (((self.Replication) == "Iterate")  or ((self.Replication) == "Default")):
				inputs = Replication.iterate(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Repeat"):
				inputs = Replication.repeat(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Interlace"):
				inputs = list(Replication.interlace(inputs))
			outputs = []
			for anInput in inputs:
				outputs.append(processItemCircularDomain(anInput, self.originLocation))
		# Rectangular Domain
		else:
			if not (self.inputs['LL Vertex'].is_linked):
				llVertexList = [topologic.Vertex.ByCoordinates(0,-1,-1)]
			else:
				llVertexList = self.inputs['LL Vertex'].sv_get(deepcopy=True)
				llVertexList = Replication.flatten(llVertexList)
			if not (self.inputs['LR Vertex'].is_linked):
				lrVertexList = [topologic.Vertex.ByCoordinates(1,0,1)]
			else:
				lrVertexList = self.inputs['LR Vertex'].sv_get(deepcopy=True)
				lrVertexList = Replication.flatten(lrVertexList)
			if not (self.inputs['UR Vertex'].is_linked):
				urVertexList = [topologic.Vertex.ByCoordinates(0,1,-1)]
			else:
				urVertexList = self.inputs['UR Vertex'].sv_get(deepcopy=True)
				urVertexList = Replication.flatten(urVertexList)
			if not (self.inputs['UL Vertex'].is_linked):
				ulVertexList = [topologic.Vertex.ByCoordinates(-1,0,1)]
			else:
				ulVertexList = self.inputs['UL Vertex'].sv_get(deepcopy=True)
				ulVertexList = Replication.flatten(ulVertexList)
			uList = self.inputs['U'].sv_get(deepcopy=True)
			uList = Replication.flatten(uList)
			vList = self.inputs['V'].sv_get(deepcopy=True)
			vList = Replication.flatten(vList)
			inputs = [originList, llVertexList, lrVertexList, urVertexList, ulVertexList, uList, vList, dirXList, dirYList, dirZList]
			if ((self.Replication) == "Trim"):
				inputs = Replication.trim(inputs)
				inputs = Replication.transposeList(inputs)
			elif (((self.Replication) == "Iterate")  or ((self.Replication) == "Default")):
				inputs = Replication.iterate(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Repeat"):
				inputs = Replication.repeat(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Interlace"):
				inputs = list(Replication.interlace(inputs))
			outputs = []
			for anInput in inputs:
				outputs.append(processItemRectangularDomain(anInput, self.originLocation))
		self.outputs['Shell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvShellHyperbolicParaboloid)

def unregister():
	bpy.utils.unregister_class(SvShellHyperbolicParaboloid)
