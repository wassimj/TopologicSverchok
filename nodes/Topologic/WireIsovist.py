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
from . import Replication

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
	viewPoint, externalBoundary, obstaclesCluster = item
	
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
	bl_icon = 'SELECT_DIFFERENCE'

	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'ViewPoint')
		self.inputs.new('SvStringsSocket', 'External Boundary')
		self.inputs.new('SvStringsSocket', 'Obstacles Cluster')
		self.outputs.new('SvStringsSocket', 'Isovist')
		self.width = 175
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Replication")
		split.row().prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs_nested = []
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		inputs_replicated = Replication.replicateInputs(inputs_flat, self.Replication)
		outputs = []
		for anInput in inputs_replicated:
			outputs.append(processItem(anInput))
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			outputs = Replication.re_interlace(outputs, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			outputs = Replication.unflatten(outputs, match_list)
		if len(outputs) == 1:
			if isinstance(outputs[0], list):
				outputs = outputs[0]
		self.outputs['Isovist'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvWireIsovist)

def unregister():
	bpy.utils.unregister_class(SvWireIsovist)
