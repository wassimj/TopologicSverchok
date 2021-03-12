import bpy
from bpy.props import BoolProperty, FloatProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last
from sverchok.utils.nodes_mixins.generating_objects import SvMeshData, SvViewerNode
from sverchok.utils.handle_blender_data import correct_collection_length
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
import sverchok.utils.meshes as me

from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph, Dictionary, Attribute, AttributeManager, VertexUtility, EdgeUtility, WireUtility, ShellUtility, CellUtility, TopologyUtility
import cppyy
from itertools import cycle
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
  return switcher.get(argument, Topology)

def fixTopologyClass(topology):
	if topology == None:
		return None
	else:
		topology.__class__ = classByType(topology.GetType())
	return topology

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


def topologyByFaces(faces, tolerance):
	output = None
	if len(faces) == 1:
		return fixTopologyClass(faces.front())
	try:
		output = Cell.ByFaces(faces)
	except:
		print("Creating a Cell failed!")
		try:
			output = CellComplex.ByFaces(faces, tolerance)
		except:
			print("Creating a CellComplex failed!")
			try:
				output = Shell.ByFaces(faces)
			except:
				print("Creating a Shell failed!")
				try:
					output = Cluster.ByTopologies(faces)
				except:
					print("Creating ANYTHING failed!")
					output = None
	return fixTopologyClass(output)

def topologyByEdges(edges):
	output = None
	if len(edges) == 1:
		return fixTopologyClass(edges.front())
	try:
		output = Wire.ByEdges(edges)
	except:
		print("Creating a Wire failed!")
		try:
			output = Cluster.ByTopologies(edges)
		except:
			print("Creating ANYTHING failed!")
			output = None
	return fixTopologyClass(output)

class SvTopologyByGeometry(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Converts the input geometry into a Topology
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

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		vertices = self.inputs['Vertices'].sv_get(deepcopy=False, default=[])[0]
		edges = self.inputs['Edges'].sv_get(deepcopy=False, default=[[]])[0]
		faces = self.inputs['Faces'].sv_get(deepcopy=False, default=[[]])[0]
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0]

		if len(vertices) > 0:
			topVerts = cppyy.gbl.std.vector[Vertex.Ptr]()
			for aVertex in vertices:
				v = Vertex.ByCoordinates(aVertex[0], aVertex[1], aVertex[2])
				topVerts.push_back(v)
		else:
			self.outputs['Topology'].sv_set([])
			end = time.time()
			print("Topology.ByGeometry Operation consumed "+str(round(end - start,2))+" seconds")
			return

		if len(faces) > 0:
			newFaces = []
			# For Topologic, the first vertex needs to be repeated for a face e.g. [0,1,2,3,4,0]
			for aFace in faces:
				aFace.append(aFace[0])
				newFaces.append(aFace)
			topFaces = cppyy.gbl.std.list[cppyy.gbl.std.list[int]]()
			for aFace in newFaces:
				f = cppyy.gbl.std.list[int]()
				for anIndex in aFace:
					f.push_back(anIndex)
				topFaces.push_back(f)
			topologies = cppyy.gbl.std.list[Topology.Ptr]()
			_ = Topology.ByVertexIndex(topVerts, topFaces, topologies)
			stlFaces = cppyy.gbl.std.list[Face.Ptr]()
			for aTopology in topologies:
				aTopology = fixTopologyClass(aTopology)
				stlFaces.push_back(aTopology)
			output = topologyByFaces(stlFaces, tol)
			self.outputs['Topology'].sv_set([output])
			end = time.time()
			print("Topology.ByGeometry Operation consumed "+str(round(end - start,2))+" seconds")
			return

		if len(edges) > 0:
			topEdges = cppyy.gbl.std.list[cppyy.gbl.std.list[int]]()
			for anEdge in edges:
				e = cppyy.gbl.std.list[int]()
				for anIndex in anEdge:
					e.push_back(anIndex)
				topEdges.push_back(e)
			topologies = cppyy.gbl.std.list[Topology.Ptr]()
			_ = Topology.ByVertexIndex(topVerts, topEdges, topologies)
			stlEdges = cppyy.gbl.std.list[Edge.Ptr]()
			for aTopology in topologies:
				aTopology = fixTopologyClass(aTopology)
				stlEdges.push_back(aTopology)
			output = topologyByEdges(stlEdges)
			self.outputs['Topology'].sv_set([output])
			end = time.time()
			print("Topology.ByGeometry Operation consumed "+str(round(end - start,2))+" seconds")
			return
		topologies = cppyy.gbl.std.list[Topology.Ptr]()
		for aVert in topVerts:
			topologies.push_back(aVert)
		output = Cluster.ByTopologies(topologies)
		self.outputs['Topology'].sv_set([output])
		end = time.time()
		print("Topology.ByGeometry Operation consumed "+str(round(end - start,2))+" seconds")


def register():
	bpy.utils.register_class(SvTopologyByGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyByGeometry)

