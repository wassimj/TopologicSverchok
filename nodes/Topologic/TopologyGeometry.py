import bpy
import bmesh
from bpy.props import FloatProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import uuid

from topologic import Topology, Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Graph, Dictionary, Attribute, AttributeManager, VertexUtility, EdgeUtility, WireUtility, FaceUtility, ShellUtility, CellUtility, TopologyUtility
import cppyy
import time

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def classByType(argument):
	switcher = {
		1: Vertex,
		2: Edge,
		4: Wire,
		8: Face,
		16: Shell,
		32: Cell,
		64: CellComplex,
		128: Cluster }
	return switcher[argument]

def fixTopologyClass(topology):
	topology.__class__ = classByType(topology.GetType())
	return topology

def getSubTopologies(topology, subTopologyClass):
	pointer = subTopologyClass.Ptr
	topologies = cppyy.gbl.std.list[pointer]()
	if subTopologyClass == Vertex:
		_ = topology.Vertices(topologies)
	elif subTopologyClass == Edge:
		_ = topology.Edges(topologies)
	elif subTopologyClass == Wire:
		_ = topology.Wires(topologies)
	elif subTopologyClass == Face:
		_ = topology.Faces(topologies)
	elif subTopologyClass == Shell:
		_ = topology.Shells(topologies)
	elif subTopologyClass == Cell:
		_ = topology.Cells(topologies)
	elif subTopologyClass == CellComplex:
		_ = topology.CellComplexes(topologies)
 
	for aTopology in topologies:
		fixTopologyClass(aTopology)
	return topologies

def triangulate(faces):
	triangles = []
	for aFace in faces:
		ib = cppyy.gbl.std.list[Wire.Ptr]()
		_ = aFace.InternalBoundaries(ib)
		if len(ib) != 0:
			faceTriangles = cppyy.gbl.std.list[Face.Ptr]()
			FaceUtility.Triangulate(aFace, 0.0, faceTriangles)
			for aFaceTriangle in faceTriangles:
				triangles.append(aFaceTriangle)
		else:
			triangles.append(aFace)
	return triangles

class SvTopologyGeometry(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Converts the input Topology into a geometry
	"""
	bl_idname = 'SvTopologyGeometry'
	bl_label = 'Topology.Geometry'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvVerticesSocket', 'Vertices')
		self.outputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Faces')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		vertices = []
		edges = []
		faces = []
		for anInput in inputs:
			vstart = time.time()
			topVerts = cppyy.gbl.std.list[Vertex.Ptr]()
			_ = anInput.Vertices(topVerts)
			for aVertex in topVerts:
				vertices.append([aVertex.X(), aVertex.Y(), aVertex.Z()])
			vend = time.time()
			print("Topology.Geometry: Creating Vertices Operation consumed "+str(round(vend - vstart,2))+" seconds")
			estart = time.time()
			topEdges = cppyy.gbl.std.list[Edge.Ptr]()
			_ = anInput.Edges(topEdges)
			for anEdge in topEdges:
				e = []
				sv = anEdge.StartVertex()
				ev = anEdge.EndVertex()
				e.append(vertices.index([sv.X(), sv.Y(), sv.Z()]))
				e.append(vertices.index([ev.X(), ev.Y(), ev.Z()]))
				edges.append(e)
			eend = time.time()
			print("Topology.Geometry: Creating Edges Operation consumed "+str(round(eend - estart,2))+" seconds")
			fstart = time.time()
			topFaces = cppyy.gbl.std.list[Face.Ptr]()
			_ = anInput.Faces(topFaces)
			for aFace in topFaces:
				ib = cppyy.gbl.std.list[Wire.Ptr]()
				_ = aFace.InternalBoundaries(ib)
				if(len(ib) > 0):
					triFaces = cppyy.gbl.std.list[Face.Ptr]()
					FaceUtility.Triangulate(aFace, 0.0, triFaces)
					for aTriFace in triFaces:
						wire = aTriFace.ExternalBoundary()
						faceVertices = getSubTopologies(wire, Vertex)
						f = []
						for aVertex in faceVertices:
							f.append(vertices.index([aVertex.X(), aVertex.Y(), aVertex.Z()]))
						faces.append(f)
				else:
					wire =  aFace.ExternalBoundary()
					faceVertices = getSubTopologies(wire, Vertex)
					f = []
					for aVertex in faceVertices:
							f.append(vertices.index([aVertex.X(), aVertex.Y(), aVertex.Z()]))
					faces.append(f)
			fend = time.time()
			print("Topology.Geometry: Creating Faces Operation consumed "+str(round(fend - fstart,2))+" seconds")
		self.outputs['Vertices'].sv_set([vertices])
		self.outputs['Edges'].sv_set([edges])
		self.outputs['Faces'].sv_set([faces])
		end = time.time()
		print("Topology.Geometry Operation consumed "+str(round(end - start,2))+" seconds")

def register():
	bpy.utils.register_class(SvTopologyGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyGeometry)

