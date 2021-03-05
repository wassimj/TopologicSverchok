import bpy
from bpy import context
import bmesh
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph, Dictionary, Attribute, AttributeManager, VertexUtility, EdgeUtility, WireUtility, ShellUtility, CellUtility, TopologyUtility

import cppyy

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
  return switcher.get(argument, Topology)

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

def topologyByGeometry(vts, eds, fcs, tol):
	py_vertices = []
	vertices = cppyy.gbl.std.list[Vertex.Ptr]()

	for v in vts:
		vertex = Vertex.ByCoordinates(v[0], v[1], v[2])
		py_vertices.append(vertex)
		vertices.push_back(vertex)

	edges = cppyy.gbl.std.list[Edge.Ptr]()
	for e in eds:
		sv = py_vertices[e[0]]
		ev = py_vertices[e[1]]
		edge = Edge.ByStartVertexEndVertex(sv, ev)
		edges.push_back(edge)

	faces = cppyy.gbl.std.list[Face.Ptr]()
	for f in fcs:
		faceVertices = []
		for v in f:
			vertex = py_vertices[v]
			faceVertices.append(vertex)
		faceEdges = edgesByVertices(faceVertices)
		face = Face.ByEdges(faceEdges)
		faces.push_back(face)

	result = []
	if len(faces) > 0:
		try:
			cc = CellComplex.ByFaces(faces, tol)
			cells = cppyy.gbl.std.list[Cell.Ptr]()
			_ = cc.Cells(cells)
			if (len(cells) == 1):
				result.append(cells.front())
			else:
				result.append(cc)
		except:
			try:
				c = Cell.ByFaces(faces, tol)
				result.append(c)
			except:
				try:
					s = Shell.ByFaces(faces, tol)
					result.append(s)
				except:
					facesAsTopologies = cppyy.gbl.std.list[Topology.Ptr]()
					for aFace in faces:
						facesAsTopologies.push_back(aFace)
					faceCluster = Cluster.ByTopologies(facesAsTopologies)
					mergedTopology = Topology.SelfMerge(faceCluster)
					mergedTopology.__class__ = classByType(mergedTopology.GetType())
					result.append(mergedTopology)

	elif len(edges) > 1:
		edgesAsTopologies = cppyy.gbl.std.list[Topology.Ptr]()
		for anEdge in edges:
			edgesAsTopologies.push_back(anEdge)
		edgeCluster = Cluster.ByTopologies(edgesAsTopologies)
		mergedTopology = Topology.SelfMerge(edgeCluster)
		mergedTopology.__class__ = classByType(mergedTopology.GetType())
		result.append(mergedTopology)
	elif len(edges) == 1:
		result.append(edges.front())
	elif len(vertices) > 1:
		verticesAsTopologies = cppyy.gbl.std.list[Topology.Ptr]()
		for aVertex in vertices:
			verticesAsTopologies.push_back(aVertex)
		vertexCluster = Cluster.ByTopologies(verticesAsTopologies)
		result.append(vertexCluster)
	elif len(vertices) == 1:
		result.append(vertices.front())
	return result

class SvTopologyByGeometry(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Converts the input geometry into a Topology
	"""
	bl_idname = 'SvTopologyByGeometry'
	bl_label = 'Topology.ByGeometry'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=5, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvVerticesSocket', 'Vertices')
		self.inputs.new('SvStringsSocket', 'Edges')
		self.inputs.new('SvStringsSocket', 'Faces')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputVertices = self.inputs['Vertices'].sv_get(deepcopy=False)
		inputEdges = self.inputs['Edges'].sv_get(deepcopy=False)
		inputFaces = self.inputs['Faces'].sv_get(deepcopy=False)
		tol = self.inputs['Tol'].sv_get(deepcopy=False)[0]
		topologies = []
		for (vts, eds, fcs) in zip(inputVertices, inputEdges, inputFaces):
			mesh = bpy.data.meshes.new("ValidationMesh")
			mesh.from_pydata(vts, eds, fcs)
			print(mesh.validate())
			if (mesh.validate()):
				print("Topologic - Topology.ByGeometry: Input Mesh is valid.")
				topology = topologyByGeometry(vts, eds, fcs, tol[0])
				topologies.append(topology)
		self.outputs['Topology'].sv_set(topologies)


def register():
	bpy.utils.register_class(SvTopologyByGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyByGeometry)

