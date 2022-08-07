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
from . import WireRectangle

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

def sliceCell(cell, width, length, height, uSides, vSides, wSides):
	origin = cell.Centroid()
	wRect = WireRectangle.processItem([origin, width*1.2, length*1.2, 0, 0, 1, "Center"])
	sliceFaces = []
	for i in range(1, wSides):
		sliceFaces.append(topologic.TopologyUtility.Translate(topologic.Face.ByExternalBoundary(wRect), 0, 0, height/wSides*i - height*0.5))
	uRect = WireRectangle.processItem([origin, height*1.2, length*1.2, 1, 0, 0, "Center"])
	for i in range(1, uSides):
		sliceFaces.append(topologic.TopologyUtility.Translate(topologic.Face.ByExternalBoundary(uRect), width/uSides*i - width*0.5, 0, 0))
	vRect = WireRectangle.processItem([origin, height*1.2, width*1.2, 0, 1, 0, "Center"])
	for i in range(1, vSides):
		sliceFaces.append(topologic.TopologyUtility.Translate(topologic.Face.ByExternalBoundary(vRect), 0, length/vSides*i - length*0.5, 0))
	sliceCluster = topologic.Cluster.ByTopologies(sliceFaces)
	cellFaces = []
	_ = cell.Faces(None, cellFaces)
	sliceFaces = sliceFaces + cellFaces
	cellComplex = topologic.CellComplex.ByFaces(sliceFaces, 0.0001)
	return cellComplex

def processItem(item):
	origin, \
	width, \
	length, \
	height, \
	uSides, \
	vSides, \
	wSides, \
	dirX, \
	dirY, \
	dirZ, \
	originLocation = item
	baseV = []
	topV = []
	xOffset = 0
	yOffset = 0
	zOffset = 0
	if originLocation == "Center":
		zOffset = -height*0.5
	elif originLocation == "LowerLeft":
		xOffset = width*0.5
		yOffset = length*0.5

	vb1 = topologic.Vertex.ByCoordinates(origin.X()-width*0.5+xOffset,origin.Y()-length*0.5+yOffset,origin.Z()+zOffset)
	vb2 = topologic.Vertex.ByCoordinates(origin.X()+width*0.5+xOffset,origin.Y()-length*0.5+yOffset,origin.Z()+zOffset)
	vb3 = topologic.Vertex.ByCoordinates(origin.X()+width*0.5+xOffset,origin.Y()+length*0.5+yOffset,origin.Z()+zOffset)
	vb4 = topologic.Vertex.ByCoordinates(origin.X()-width*0.5+xOffset,origin.Y()+length*0.5+yOffset,origin.Z()+zOffset)

	vt1 = topologic.Vertex.ByCoordinates(origin.X()-width*0.5+xOffset,origin.Y()-length*0.5+yOffset,origin.Z()+height+zOffset)
	vt2 = topologic.Vertex.ByCoordinates(origin.X()+width*0.5+xOffset,origin.Y()-length*0.5+yOffset,origin.Z()+height+zOffset)
	vt3 = topologic.Vertex.ByCoordinates(origin.X()+width*0.5+xOffset,origin.Y()+length*0.5+yOffset,origin.Z()+height+zOffset)
	vt4 = topologic.Vertex.ByCoordinates(origin.X()-width*0.5+xOffset,origin.Y()+length*0.5+yOffset,origin.Z()+height+zOffset)
	baseWire = wireByVertices([vb1, vb2, vb3, vb4])
	topWire = wireByVertices([vt1, vt2, vt3, vt4])
	wires = [baseWire, topWire]
	prism =  topologic.CellUtility.ByLoft(wires)
	prism = sliceCell(prism, width, length, height, uSides, vSides, wSides)
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
	prism = topologic.TopologyUtility.Rotate(prism, origin, 0, 1, 0, theta)
	prism = topologic.TopologyUtility.Rotate(prism, origin, 0, 0, 1, phi)
	return prism

originLocations = [("Bottom", "Bottom", "", 1),("Center", "Center", "", 2),("LowerLeft", "Lower Left", "", 3)]
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvCellComplexPrism(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Prism (Cell) from the input cuboid parameters    
	"""
	bl_idname = 'SvCellComplexPrism'
	bl_label = 'CellComplex.Prism'
	Width: FloatProperty(name="Width", default=1, min=0.0001, precision=4, update=updateNode)
	Length: FloatProperty(name="Length", default=1, min=0.0001, precision=4, update=updateNode)
	Height: FloatProperty(name="Height", default=1, min=0.0001, precision=4, update=updateNode)
	USides: IntProperty(name="U Sides", default=2, min=1, update=updateNode)
	VSides: IntProperty(name="V Sides", default=2, min=1, update=updateNode)
	WSides: IntProperty(name="W Sides", default=2, min=1, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)

	originLocation: EnumProperty(name="Origin Location", description="Origing Location", default="Bottom", items=originLocations, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Width').prop_name = 'Width'
		self.inputs.new('SvStringsSocket', 'Length').prop_name = 'Length'
		self.inputs.new('SvStringsSocket', 'Height').prop_name = 'Height'
		self.inputs.new('SvStringsSocket', 'U Sides').prop_name = 'USides'
		self.inputs.new('SvStringsSocket', 'V Sides').prop_name = 'VSides'
		self.inputs.new('SvStringsSocket', 'W Sides').prop_name = 'WSides'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.outputs.new('SvStringsSocket', 'CellComplex')

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
		widthList = self.inputs['Width'].sv_get(deepcopy=True)
		lengthList = self.inputs['Length'].sv_get(deepcopy=True)
		heightList = self.inputs['Height'].sv_get(deepcopy=True)
		uSidesList = self.inputs['U Sides'].sv_get(deepcopy=True)
		vSidesList = self.inputs['V Sides'].sv_get(deepcopy=True)
		wSidesList = self.inputs['W Sides'].sv_get(deepcopy=True)
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)

		originList = flatten(originList)
		widthList = flatten(widthList)
		lengthList = flatten(lengthList)
		heightList = flatten(heightList)
		uSidesList = flatten(uSidesList)
		vSidesList = flatten(vSidesList)
		wSidesList = flatten(wSidesList)
		dirXList = flatten(dirXList)
		dirYList = flatten(dirYList)
		dirZList = flatten(dirZList)
		inputs = [originList, widthList, lengthList, heightList, uSidesList, vSidesList, wSidesList, dirXList, dirYList, dirZList]
		if ((self.Replication) == "Default"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		if ((self.Replication) == "Trim"):
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
			outputs.append(processItem(anInput+[self.originLocation]))
		self.outputs['CellComplex'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellComplexPrism)

def unregister():
	bpy.utils.unregister_class(SvCellComplexPrism)
