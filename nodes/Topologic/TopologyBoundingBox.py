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

def processItem(item):
	vertices = []
	_ = item.Vertices(None, vertices)
	x = []
	y = []
	z = []
	for aVertex in vertices:
		x.append(aVertex.X())
		y.append(aVertex.Y())
		z.append(aVertex.Z())
	minX = min(x)
	minY = min(y)
	minZ = min(z)
	maxX = max(x)
	maxY = max(y)
	maxZ = max(z)

	vb1 = topologic.Vertex.ByCoordinates(minX, minY, minZ)
	vb2 = topologic.Vertex.ByCoordinates(maxX, minY, minZ)
	vb3 = topologic.Vertex.ByCoordinates(maxX, maxY, minZ)
	vb4 = topologic.Vertex.ByCoordinates(minX, maxY, minZ)

	vt1 = topologic.Vertex.ByCoordinates(minX, minY, maxZ)
	vt2 = topologic.Vertex.ByCoordinates(maxX, minY, maxZ)
	vt3 = topologic.Vertex.ByCoordinates(maxX, maxY, maxZ)
	vt4 = topologic.Vertex.ByCoordinates(minX, maxY, maxZ)
	baseWire = wireByVertices([vb1, vb2, vb3, vb4])
	topWire = wireByVertices([vt1, vt2, vt3, vt4])
	wires = [baseWire, topWire]
	return ([topologic.CellUtility.ByLoft(wires), vb1, vt3])


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

class SvTopologyBoundingBox(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cell that represents the bounding box of the input Topology    
	"""
	bl_idname = 'SvTopologyBoundingBox'
	bl_label = 'Topology.BoundingBox'
	
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Cell')
		self.outputs.new('SvStringsSocket', 'Min Vertex')
		self.outputs.new('SvStringsSocket', 'Max Vertex')


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		cellOutputs = []
		minVertexOutputs = []
		maxVertexOutputs = []
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		for anInput in inputs:
			output = processItem(anInput)
			cellOutputs.append(output[0])
			minVertexOutputs.append(output[1])
			maxVertexOutputs.append(output[2])
		self.outputs['Cell'].sv_set(cellOutputs)
		self.outputs['Min Vertex'].sv_set(minVertexOutputs)
		self.outputs['Max Vertex'].sv_set(maxVertexOutputs)

def register():
	bpy.utils.register_class(SvTopologyBoundingBox)

def unregister():
	bpy.utils.unregister_class(SvTopologyBoundingBox)
