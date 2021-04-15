import bpy
import bmesh
from bpy.props import FloatProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import uuid
from sverchok.utils.sv_mesh_utils import get_unique_faces

from topologic import Topology, Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Graph, Dictionary, Attribute, AttributeManager, VertexUtility, EdgeUtility, WireUtility, FaceUtility, ShellUtility, CellUtility, TopologyUtility
import cppyy

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
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		vertices = []
		edges = []
		faces = []
		for anInput in inputs: # Collect all the vertices from all the inputs
			if anInput == None:
				vertices.append([])
				continue
			topVerts = cppyy.gbl.std.list[Vertex.Ptr]()
			if (anInput.GetType() == 1): #input is a vertex, just add it and process it
				topVerts.push_back(anInput)
			else:
				_ = anInput.Vertices(topVerts)
			for aVertex in topVerts:
				try:
					vertices.index([aVertex.X(), aVertex.Y(), aVertex.Z()]) # Vertex already in list
				except:
					vertices.append([aVertex.X(), aVertex.Y(), aVertex.Z()]) # Vertex not in list, add it.

		for anInput in inputs:
			if anInput == None:
				edges.append([])
				faces.append([])
				continue
			topEdges = cppyy.gbl.std.list[Edge.Ptr]()
			if (anInput.GetType() == 2): #Input is an Edge, just add it and process it
				topEdges.push_back(anInput)
			elif (anInput.GetType() > 2):
				_ = anInput.Edges(topEdges)
			for anEdge in topEdges:
				e = []
				sv = anEdge.StartVertex()
				ev = anEdge.EndVertex()
				try:
					svIndex = vertices.index([sv.X(), sv.Y(), sv.Z()])
				except:
					vertices.append([sv.X(), sv.Y(), sv.Z()])
					svIndex = len(vertices)-1
				try:
					evIndex = vertices.index([ev.X(), ev.Y(), ev.Z()])
				except:
					vertices.append([ev.X(), ev.Y(), ev.Z()])
					evIndex = len(vertices)-1
				e.append(svIndex)
				e.append(evIndex)
				if ([e[0], e[1]] not in edges) and ([e[1], e[0]] not in edges):
					edges.append(e)
			topFaces = cppyy.gbl.std.list[Face.Ptr]()
			if (anInput.GetType() == 8): # Input is a Face, just add it and process it
				topFaces.push_back(anInput)
			elif (anInput.GetType() > 8):
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
							try:
								fVertexIndex = vertices.index([aVertex.X(), aVertex.Y(), aVertex.Z()])
							except:
								vertices.append([aVertex.X(), aVertex.Y(), aVertex.Z()])
								fVertexIndex = len(vertices)-1
							f.append(fVertexIndex)
						faces.append(f)
				else:
					wire =  aFace.ExternalBoundary()
					faceVertices = getSubTopologies(wire, Vertex)
					f = []
					for aVertex in faceVertices:
						try:
							fVertexIndex = vertices.index([aVertex.X(), aVertex.Y(), aVertex.Z()])
						except:
							vertices.append([aVertex.X(), aVertex.Y(), aVertex.Z()])
							fVertexIndex = len(vertices)-1
						f.append(fVertexIndex)
					faces.append(f)
		
		faces = get_unique_faces(faces) #Make sure we do not accidentally have duplicate faces
		self.outputs['Vertices'].sv_set([vertices])
		self.outputs['Edges'].sv_set([edges])
		self.outputs['Faces'].sv_set([faces])

def register():
	bpy.utils.register_class(SvTopologyGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyGeometry)

