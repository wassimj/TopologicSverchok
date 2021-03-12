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

def edgesByVertices(vertices):
	edges = cppyy.gbl.std.list[Edge.Ptr]()
	for i in range(len(vertices)-1):
		v1 = vertices[i]
		v2 = vertices[i+1]
		e1 = Edge.ByStartVertexEndVertex(v1, v2)
		edges.push_back(e1)
	# connect the last vertex to the first one
	v1 = vertices[len(vertices)-1]
	v2 = vertices[0]
	e1 = Edge.ByStartVertexEndVertex(v1, v2)
	edges.push_back(e1)
	return edges

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

def vertexIndex(v, vertices, tolerance):
	index = None
	v._class__ = Vertex
	i = 0
	for aVertex in vertices:
		aVertex.__class__ = Vertex
		d = VertexUtility.Distance(v, aVertex)
		if d <= tolerance:
			index = i
			break
		i = i+1
	return index

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

'''
def meshData(topology):
    type = classByType(topology.GetType())
    if type == Cluster or type == CellComplex or type == Cell or type == Shell:
        topFaces1 = getSubTopologies(topology, Face)
        topFaces = triangulate(topFaces1)
        topEdges = getSubTopologies(topology, Edge)
        topVertices = getSubTopologies(topology, Vertex)
    elif type == Face:
        topFaces1 = cppyy.gbl.std.list[Face.Ptr]()
        topFaces1.push_back(topology)
        topFaces = triangulate(topFaces1)
        topEdges = getSubTopologies(topology, Edge)
        topVertices = getSubTopologies(topology, Vertex)
    elif type == Wire:
        topFaces = []
        topEdges = getSubTopologies(topology, Edge)
        topVertices = getSubTopologies(topology, Vertex)
    elif type == Edge:
        topFaces = []
        topEdges = cppyy.gbl.std.list[Edge.Ptr]()
        topEdges.push_back(topology)
        topVertices = getSubTopologies(topology, Vertex)
    elif type == Vertex:
        topFaces = []
        topEdges = []
        topVertices = cppyy.gbl.std.list[Vertex.Ptr]()
        topVertices.push_back(topology)
    else:
        topFaces = []
        topEdges = []
        topVertices = []
    vertices = []
    for aVertex in topVertices:
        vertices.append(tuple([aVertex.X(), aVertex.Y(), aVertex.Z()]))
    faces = []
    for aFace in topFaces:
        wire = aFace.ExternalBoundary()
        faceVertices = getSubTopologies(wire, Vertex)
        tempList = []
        for aVertex in faceVertices:
            index = vertexIndex(aVertex, topVertices, 0.0001)
            tempList.append(index)
        faces.append(tuple(tempList))
    edges = []
    for anEdge in topEdges:
        edgeVertices = getSubTopologies(anEdge, Vertex)
        tempList = []
        for aVertex in edgeVertices:
            index = vertexIndex(aVertex, topVertices, 0.0001)
            tempList.append(index)
        edges.append(tuple(tempList))
    return [vertices, edges, faces]

def processItem(topology, vertices, edges, faces):
	vts = []
	eds = []
	fcs = []
	md = meshData(topology)
	vertices.append(md[0])
	edges.append(md[1])
	faces.append(md[2])
	return [None, vertices, edges, faces]

def recur(input, vertices, edges, faces):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			dummy1, vertices, edges, faces = recur(anItem, vertices, edges, faces)
	else:
		dummy1, vertices, edges, faces = processItem(input, vertices, edges, faces)
	return [None, vertices, edges, faces]
'''

class SvTopologyGeometry(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Converts the input Topology into a geometry
	"""
	bl_idname = 'SvTopologyGeometry'
	bl_label = 'Topology.Geometry'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvVerticesSocket', 'Vertices')
		self.outputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Faces')
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0]


	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		vertices = []
		edges = []
		faces = []
		for anInput in inputs:
			topVerts = cppyy.gbl.std.list[Vertex.Ptr]()
			_ = anInput.Vertices(topVerts)
			for aVertex in topVerts:
				vertices.append([aVertex.X(), aVertex.Y(), aVertex.Z()])
			topFace = cppyy.gbl.std.list[Face.Ptr]()
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
							f.append(vertexIndex(aVertex, topVerts, tol))
						faces.append(f)
				else:
					wire =  aFace.ExternalBoundary()
					faceVertices = getSubTopologies(wire, Vertex)
					f = []
					for aVertex in faceVertices:
						f.append(vertexIndex(aVertex, topVerts, tol))
					f.append(f[0])
					faces.append(f)
			topEdges = cppyy.gbl.std.list[Edge.Ptr]()
			_ = anInput.Edges()
			for anEdge in topEdges:
				e = []
				sv = anEdge.StartVertex()
				ev = anEdge.EndVertex()
				e.append(vertexIndex(sv, topVerts, tol))
				e.append(vertexIndex(ev, topVerts, tol))
				edges.append(e)
		self.outputs['Vertices'].sv_set(vertices)
		self.outputs['Edges'].sv_set(edges)
		self.outputs['Faces'].sv_set(faces)
		end = time.time()
		print("Topology.Geometry Operation consumed "+str(round(end - start,2))+" seconds")

def register():
	bpy.utils.register_class(SvTopologyGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyGeometry)

