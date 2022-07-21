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
			# print(base,y)
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

def createCone(baseWire, topWire, baseVertex, topVertex, tol):
	if baseWire == None and topWire == None:
		raise Exception("Cell.Cone - Error: Both radii of the cone cannot be zero at the same time")
	elif baseWire == None:
		apex = baseVertex
		wire = topWire
	elif topWire == None:
		apex = topVertex
		wire = baseWire
	else:
		return topologic.CellUtility.ByLoft([baseWire, topWire])

	vertices = []
	_ = wire.Vertices(None,vertices)
	faces = [topologic.Face.ByExternalBoundary(wire)]
	for i in range(0, len(vertices)-1):
		w = wireByVertices([apex, vertices[i], vertices[i+1]])
		f = topologic.Face.ByExternalBoundary(w)
		faces.append(f)
	w = wireByVertices([apex, vertices[-1], vertices[0]])
	f = topologic.Face.ByExternalBoundary(w)
	faces.append(f)
	return topologic.Cell.ByFaces(faces, tol)

def processItem(item, originLocation):
	origin = item[0]
	baseRadius = item[1]
	topRadius = item[2]
	height = item[3]
	sides = item[4]
	dirX = item[5]
	dirY = item[6]
	dirZ = item[7]
	tol = item[8]
	baseV = []
	topV = []
	xOffset = 0
	yOffset = 0
	zOffset = 0
	if originLocation == "Center":
		zOffset = -height*0.5
	elif originLocation == "LowerLeft":
		xOffset = max(baseRadius, topRadius)
		yOffset = max(baseRadius, topRadius)

	baseZ = origin.Z() + zOffset
	topZ = origin.Z() + zOffset + height
	for i in range(sides):
		angle = math.radians(360/sides)*i
		if baseRadius > 0:
			baseX = math.sin(angle)*baseRadius + origin.X() + xOffset
			baseY = math.cos(angle)*baseRadius + origin.Y() + yOffset
			baseZ = origin.Z() + zOffset
			baseV.append(topologic.Vertex.ByCoordinates(baseX,baseY,baseZ))
		if topRadius > 0:
			topX = math.sin(angle)*topRadius + origin.X() + xOffset
			topY = math.cos(angle)*topRadius + origin.Y() + yOffset
			topV.append(topologic.Vertex.ByCoordinates(topX,topY,topZ))

	if baseRadius > 0:
		baseWire = wireByVertices(baseV)
	else:
		baseWire = None
	if topRadius > 0:
		topWire = wireByVertices(topV)
	else:
		topWire = None
	baseVertex = topologic.Vertex.ByCoordinates(origin.X()+xOffset, origin.Y()+yOffset, origin.Z()+zOffset)
	topVertex = topologic.Vertex.ByCoordinates(origin.X()+xOffset, origin.Y()+yOffset, origin.Z()+zOffset+height)
	cone = createCone(baseWire, topWire, baseVertex, topVertex, tol)
	if cone == None:
		raise Exception("Cell.Cone - Error: Could not create cone")
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
	cone = topologic.TopologyUtility.Rotate(cone, origin, 0, 1, 0, theta)
	cone = topologic.TopologyUtility.Rotate(cone, origin, 0, 0, 1, phi)
	return cone

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

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
originLocations = [("Bottom", "Bottom", "", 1),("Center", "Center", "", 2),("LowerLeft", "LowerLeft", "", 3)]

class SvCellCone(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cone (Cell) from the input parameters    
	"""
	bl_idname = 'SvCellCone'
	bl_label = 'Cell.Cone'
	BaseRadius: FloatProperty(name="Base Radius", default=1, min=0, precision=4, update=updateNode)
	TopRadius: FloatProperty(name="Top Radius", default=0, min=0, precision=4, update=updateNode)
	Height: FloatProperty(name="Height", default=1, min=0.0001, precision=4, update=updateNode)
	Sides: IntProperty(name="Sides", default=16, min=3, max=360, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	originLocation: EnumProperty(name="originLocation", description="Specify origin location", default="Bottom", items=originLocations, update=updateNode)
	Tol: FloatProperty(name='Tolerance', default=0.0001, min=0, precision=4, update=updateNode)

	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)


	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Base Radius').prop_name = 'BaseRadius'
		self.inputs.new('SvStringsSocket', 'Top Radius').prop_name = 'TopRadius'
		self.inputs.new('SvStringsSocket', 'Height').prop_name = 'Height'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'Sides'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Cell')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "originLocation",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not (self.inputs['Origin'].is_linked):
			originList = [topologic.Vertex.ByCoordinates(0,0,0)]
		else:
			originList = self.inputs['Origin'].sv_get(deepcopy=True)
		baseRadiusList = self.inputs['Base Radius'].sv_get(deepcopy=True)
		topRadiusList = self.inputs['Top Radius'].sv_get(deepcopy=True)
		heightList = self.inputs['Height'].sv_get(deepcopy=True)
		sidesList = self.inputs['Sides'].sv_get(deepcopy=True)
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)
		tolList = self.inputs['Tol'].sv_get(deepcopy=True)
		originList = flatten(originList)
		baseRadiusList = flatten(baseRadiusList)
		topRadiusList = flatten(topRadiusList)
		heightList = flatten(heightList)
		sidesList = flatten(sidesList)
		dirXList = flatten(dirXList)
		dirYList = flatten(dirYList)
		dirZList = flatten(dirZList)
		tolList = flatten(tolList)

		inputs = [originList, baseRadiusList, topRadiusList, heightList, sidesList, dirXList, dirYList, dirZList, tolList]
		if ((self.Replication) == "Default"):
			inputs = iterate(inputs)
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
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, self.originLocation))
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellCone)

def unregister():
	bpy.utils.unregister_class(SvCellCone)
