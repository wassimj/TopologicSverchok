import bpy
from bpy.props import BoolProperty, FloatProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last
from sverchok.utils.nodes_mixins.generating_objects import SvMeshData, SvViewerNode
from sverchok.utils.handle_blender_data import correct_collection_length
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
import sverchok.utils.meshes as me

import topologic
#from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph, Dictionary, Attribute, AttributeManager, VertexUtility, EdgeUtility, WireUtility, ShellUtility, CellUtility, TopologyUtility
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph, Dictionary
from itertools import cycle

def edgesByVertices(vertices, topVerts):
    edges = []
    for i in range(len(vertices)-1):
        v1 = vertices[i]
        v2 = vertices[i+1]
        e1 = Edge.ByStartVertexEndVertex(topVerts[v1], topVerts[v2])
        edges.append(e1)
    # connect the last vertex to the first one
    v1 = vertices[-1]
    v2 = vertices[0]
    e1 = Edge.ByStartVertexEndVertex(topVerts[v1], topVerts[v2])
    edges.append(e1)
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


def topologyByFaces(faces, tolerance):
	output = None
	if len(faces) == 1:
		return faces[0]
	try:
		output = Cell.ByFaces(faces, tolerance)
	except:
		try:
			output = CellComplex.ByFaces(faces, tolerance)
		except:
			try:
				output = Shell.ByFaces(faces, tolerance)
			except:
				try:
					output = Cluster.ByTopologies(faces)
					output = output.SelfMerge()
				except:
					print("ERROR: Could not create any topology from the input faces!")
					output = None
	return output

def topologyByEdges(edges):
	output = None
	if len(edges) == 1:
		return edges[0]
	output = Cluster.ByTopologies(edges)
	output = output.SelfMerge()
	return output

class SvTopologyByGeometry(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology from the input geometry
	"""
	bl_idname = 'SvTopologyByGeometry'
	bl_label = 'Topology.ByGeometry'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertices')
		self.inputs.new('SvStringsSocket', 'Edges')
		self.inputs.new('SvStringsSocket', 'Faces')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Vertices')
		self.outputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Faces')


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		vertices = []
		edges = []
		faces = []
		if (self.inputs['Vertices'].is_linked):
			vertices = self.inputs['Vertices'].sv_get(deepcopy=False, default=[])[0]
		if (self.inputs['Edges'].is_linked):
			edges = self.inputs['Edges'].sv_get(deepcopy=False, default=[])[0]
		if (self.inputs['Faces'].is_linked):
			faces = self.inputs['Faces'].sv_get(deepcopy=False, default=[])[0]
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0]

		if len(vertices) > 0:
			topVerts = []
			for aVertex in vertices:
				v = Vertex.ByCoordinates(aVertex[0], aVertex[1], aVertex[2])
				topVerts.append(v)
			self.outputs['Vertices'].sv_set(topVerts)
		else:
			self.outputs['Topology'].sv_set([])
			return

		if len(faces) > 0:
			topFaces = []
			for aFace in faces:
				faceEdges = edgesByVertices(aFace, topVerts)
				faceWire = Wire.ByEdges(faceEdges)
				topFace = Face.ByExternalBoundary(faceWire)
				topFaces.append(topFace)
			output = topologyByFaces(topFaces, tol)
			self.outputs['Faces'].sv_set(topFaces)
			self.outputs['Topology'].sv_set([output])
			return

		if len(edges) > 0:
			topEdges = []
			for anEdge in edges:
				topEdge = Edge.ByStartVertexEndVertex(topVerts[anEdge[0]], topVerts[anEdge[1]])
				topEdges.append(topEdge)
			output = topologyByEdges(topEdges)
			self.outputs['Edges'].sv_set(topEdges)
			self.outputs['Topology'].sv_set([output])
			return
		output = Cluster.ByTopologies(topVerts)
		self.outputs['Topology'].sv_set([output])


def register():
	bpy.utils.register_class(SvTopologyByGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyByGeometry)

