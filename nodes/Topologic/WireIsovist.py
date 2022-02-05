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

def nearestVertex(v, vList):
	distances = []
	indexList = list(range(len(vList)))
	for vertex in vList:
		distances.append(topologic.VertexUtility.Distance(v, vertex))
	z = [x for _, x in sorted(zip(distances, indexList))]
	return vList[z[0]]

def toDegrees(ang):
	import math
	return ang * 180 / math.pi

def angleBetweenEdges(e1, e2, tolerance):
	a = e1.EndVertex().X() - e1.StartVertex().X()
	b = e1.EndVertex().Y() - e1.StartVertex().Y()
	c = e1.EndVertex().Z() - e1.StartVertex().Z()
	d = topologic.VertexUtility.Distance(e1.EndVertex(), e2.StartVertex())
	if d <= tolerance:
		d = e2.StartVertex().X() - e2.EndVertex().X()
		e = e2.StartVertex().Y() - e2.EndVertex().Y()
		f = e2.StartVertex().Z() - e2.EndVertex().Z()
	else:
		d = e2.EndVertex().X() - e2.StartVertex().X()
		e = e2.EndVertex().Y() - e2.StartVertex().Y()
		f = e2.EndVertex().Z() - e2.StartVertex().Z()
	dotProduct = a*d + b*e + c*f
	modOfVector1 = math.sqrt( a*a + b*b + c*c)*math.sqrt(d*d + e*e + f*f) 
	angle = dotProduct/modOfVector1
	angleInDegrees = math.degrees(math.acos(angle))
	return angleInDegrees

def normalizeEdge(e):
	length = topologic.EdgeUtility.Length(e)
	ev = e.EndVertex()
	scaleFactor = 1/length
	newEv = topologic.TopologyUtility.Scale(ev, e.StartVertex(), scaleFactor, scaleFactor, scaleFactor)
	newEdge = topologic.Edge.ByStartVertexEndVertex(e.StartVertex(), newEv)
	return newEdge

def compassAngle(e1, e2):
	ne1 = normalizeEdge(e1)
	ne2 = normalizeEdge(e2)
	deltaX = ne2.EndVertex().X() - ne1.EndVertex().X()
	deltaY = ne2.EndVertex().Y() - ne1.EndVertex().Y()
	degrees_temp = math.atan2(deltaX, deltaY)/math.pi*360
	#print(degrees_temp)
	if degrees_temp < 0:
		degrees_final = 360 + degrees_temp
	else:
		degrees_final = degrees_temp
	print(degrees_final)
	return degrees_final

def vertexPartofFace(vertex, face, tolerance):
	vertices = []
	_ = face.Vertices(None, vertices)
	for v in vertices:
		if topologic.VertexUtility.Distance(vertex, v) < tolerance:
			return True
	return False

def processItem(item):
	viewPoint = item[0]
	externalBoundary = item[1]
	obstaclesCluster = item[2]
	internalBoundaries = []
	_ = obstaclesCluster.Wires(None, internalBoundaries)
	internalVertices = []
	_ = obstaclesCluster.Vertices(None, internalVertices)
	# 1. Create a Face with external and internal boundaries
	face = topologic.Face.ByExternalInternalBoundaries(externalBoundary, internalBoundaries, False)
	# 2. Draw Rays from viewpoint through each Vertex of the obstacles extending to the External Boundary
	#	2.1 Get the Edges and Vertices of the External Boundary
	exBoundaryEdges = []
	_ = externalBoundary.Edges(None, exBoundaryEdges)
	exBoundaryVertices = []
	_ = externalBoundary.Vertices(None, exBoundaryVertices)
	testTopologies = exBoundaryEdges+exBoundaryVertices
	#	1.2 Find the maximum distance from the viewpoint to the edges and vertices of the external boundary
	distances = []
	for x in testTopologies:
		distances.append(topologic.VertexUtility.Distance(viewPoint, x))
	maxDistance = max(distances)*1.5
	#	1.3 Shoot rays and intersect with the external boundary
	rays = []
	for aVertex in (internalVertices+exBoundaryVertices):
		d = topologic.VertexUtility.Distance(viewPoint, aVertex)
		if d > 0:
			scaleFactor = maxDistance/d
			newV = topologic.TopologyUtility.Scale(aVertex, viewPoint, scaleFactor, scaleFactor, scaleFactor)
			ray = topologic.Edge.ByStartVertexEndVertex(viewPoint, newV)
			topologyC = ray.Intersect(externalBoundary, False)
			vertices = []
			_ = topologyC.Vertices(None, vertices)
			if topologyC:
				rays.append(topologic.Edge.ByStartVertexEndVertex(viewPoint, vertices[0]))
			rays.append(topologic.Edge.ByStartVertexEndVertex(viewPoint, aVertex))
	rayEdges = []
	for r in rays:
		a = r.Difference(obstaclesCluster, False)
		edges = []
		_ = a.Edges(None, edges)
		w = None
		try:
			w = topologic.Wire.ByEdges(edges)
			rayEdges = rayEdges + edges
		except:
			c = topologic.Cluster.ByTopologies(edges)
			c = c.SelfMerge()
			wires = []
			_ = c.Wires(None, wires)
			if len(wires) > 0:
				edges = []
				_ = wires[0].Edges(None, edges)
				rayEdges = rayEdges + edges
			else:
				for e in edges:
					vertices = []
					e.Vertices(None, vertices)
					for v in vertices:
						if topologic.VertexUtility.Distance(viewPoint, v) < 0.0001:
							rayEdges.append(e)
	rayCluster = topologic.Cluster.ByTopologies(rayEdges)
	#return rayCluster
	shell = face.Slice(rayCluster, False)
	faces = []
	_ = shell.Faces(None, faces)
	finalFaces = []
	for aFace in faces:
		if vertexPartofFace(viewPoint, aFace, 0.001):
			finalFaces.append(aFace)
	return finalFaces

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvWireIsovist(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates an Isovist (Face) from the input origin    
	"""
	bl_idname = 'SvWireIsovist'
	bl_label = 'Wire.Isovist'
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'ViewPoint')
		self.inputs.new('SvStringsSocket', 'External Boundary')
		self.inputs.new('SvStringsSocket', 'Obstacles Cluster')
		self.outputs.new('SvStringsSocket', 'Isovist')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		vpList = self.inputs['ViewPoint'].sv_get(deepcopy=True)
		exBoundaryList = self.inputs['External Boundary'].sv_get(deepcopy=True)
		obstaclesClusterList = self.inputs['Obstacles Cluster'].sv_get(deepcopy=True)
		vpList = flatten(vpList)
		exBoundaryList = flatten(exBoundaryList)
		obstaclesClusterList = flatten(obstaclesClusterList)
		inputs = [vpList, exBoundaryList, obstaclesClusterList]
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
			outputs.append(processItem(anInput))
		self.outputs['Isovist'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvWireIsovist)

def unregister():
	bpy.utils.unregister_class(SvWireIsovist)
