import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from . import WireByVertices, TopologyTransform, MatrixByTranslation, MatrixMultiply
from mathutils import Matrix

import math
try:
	 from pyobb.obb import OBB
except:
	raise Exception("No pyobb")

def wireByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def processItem(item):
	topology, optimized = item
	vertices = []
	_ = topology.Vertices(None, vertices)
	c = topology.Centroid()
	mat = Matrix([[1,0,0,c.X()*-1.0],
            [0,1,0,c.Y()*-1.0],
            [0,0,1,c.Z()*-1.0],
			[0,0,0,1]])
	if optimized:
		points = []
		for aVertex in vertices:
			points.append((aVertex.X(), aVertex.Y(), aVertex.Z()))
		obb = OBB.build_from_points(points)
		rotation = obb.rotation.tolist()
		centroid = obb.centroid
		print(rotation)
		print(centroid)
		new_rows = []
		for i, row in enumerate(rotation):
			row.append(0)
			new_rows.append(row)
		new_rows.append([0,0,0,1])
		rotation = Matrix(new_rows)
		translation = MatrixByTranslation.processItem([centroid[0]*-1.0, centroid[1]*-1.0, centroid[2]*-1.0])
		mat = MatrixMultiply.processItem([rotation, translation])
		print(mat)
		obb_vertices = []
		for obb_point in obb.points:
			obb_vertices.append(topologic.Vertex.ByCoordinates(obb_point[0], obb_point[1], obb_point[2]))
		baseWire = WireByVertices.processItem([topologic.Cluster.ByTopologies(obb_vertices[0:4]),True])
		topWire = WireByVertices.processItem([topologic.Cluster.ByTopologies(obb_vertices[4:]),True])
		
	else:
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
	cell = topologic.CellUtility.ByLoft(wires)
	return [cell, mat]


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

class SvTopologyBoundingBox(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cell that represents the bounding box of the input Topology    
	"""
	bl_idname = 'SvTopologyBoundingBox'
	bl_label = 'Topology.BoundingBox'
	optimized: BoolProperty(name="Optimized", default=False, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Optimized').prop_name = 'optimized'
		self.outputs.new('SvStringsSocket', 'Cell')
		self.outputs.new('SvMatrixSocket', 'Matrix')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		optimized = self.inputs['Optimized'].sv_get(deepcopy=False)[0][0]
		cellOutputs = []
		matOutputs = []

		for anInput in inputs:
			output = processItem([anInput, optimized])
			cellOutputs.append(output[0])
			matOutputs.append(output[1])
		self.outputs['Cell'].sv_set(cellOutputs)
		self.outputs['Matrix'].sv_set(matOutputs)

def register():
	bpy.utils.register_class(SvTopologyBoundingBox)

def unregister():
	bpy.utils.unregister_class(SvTopologyBoundingBox)
