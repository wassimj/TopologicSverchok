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
import collections

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


def edgesByVertices(vertices, topVerts):
	edges = cppyy.gbl.std.list[Edge.Ptr]()
	for i in range(len(vertices)-1):
		v1 = vertices[i]
		v2 = vertices[i+1]
		e1 = Edge.ByStartVertexEndVertex(topVerts[v1], topVerts[v2])
		edges.push_back(e1)
	# connect the last vertex to the first one
	v1 = vertices[-1]
	v2 = vertices[0]
	e1 = Edge.ByStartVertexEndVertex(topVerts[v1], topVerts[v2])
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
		try:
			output = CellComplex.ByFaces(faces, tolerance)
		except:
			try:
				output = Shell.ByFaces(faces)
			except:
				try:
					output = Cluster.ByTopologies(faces)
				except:
					print("ERROR: Could not create any topology from the input faces!")
					output = None
	return fixTopologyClass(output)



def topologyByEdges(edges):
	output = None
	if len(edges) == 1:
		return fixTopologyClass(edges.front())
	try:
		output = Wire.ByEdges(edges)
	except:
		try:
			output = Cluster.ByTopologies(edges)
		except:
			print("ERROR: Could not create any topology from the input edges!")
			output = None
	return fixTopologyClass(output)

def processItem(item, tol):
	vertices = item[0]
	edges = item[1]
	faces = item[2]
	topVerts = cppyy.gbl.std.vector[Vertex.Ptr]()
	topFaces = cppyy.gbl.std.list[Face.Ptr]()
	topEdges = cppyy.gbl.std.list[Edge.Ptr]()
	output = None
	if len(vertices) > 0:
		for aVertex in vertices:
			v = Vertex.ByCoordinates(aVertex[0], aVertex[1], aVertex[2])
			topVerts.push_back(v)
	else: #No Vertices means no Topology
		return None
	# Faces exist, so try to make a topology out of the faces
	if len(faces) > 0:
		for aFace in faces:
			faceEdges = edgesByVertices(aFace, topVerts)
			faceWire = Wire.ByEdges(faceEdges)
			topFace = Face.ByExternalBoundary(faceWire)
			topFaces.push_back(topFace)
		output = topologyByFaces(topFaces, tol)
		return output
	# Faces do not exist, so try to make a topology out of the edges
	if len(edges) > 0:
		for anEdge in edges:
			topEdge = Edge.ByStartVertexEndVertex(topVerts[anEdge[0]], topVerts[anEdge[1]])
			topEdges.push_back(topEdge)
		output = topologyByEdges(topEdges)
		return output
	# No Edges or Faces exist, so try to make a Cluster of the Vertices
	topologies = cppyy.gbl.std.list[Topology.Ptr]()
	for aVert in topVerts:
		topologies.push_back(aVert)
	output = Cluster.ByTopologies(topologies)
	return output

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

class SvTopologyByGeometryNew(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology from the input geometry
	"""
	bl_idname = 'SvTopologyByGeometryNew'
	bl_label = 'Topology.ByGeometryNew'
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
			vertices = self.inputs['Vertices'].sv_get(deepcopy=False, default=[])
		if (self.inputs['Edges'].is_linked):
			edges = self.inputs['Edges'].sv_get(deepcopy=False, default=[])
		if (self.inputs['Faces'].is_linked):
			faces = self.inputs['Faces'].sv_get(deepcopy=False, default=[])
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0]
		matchLengths([vertices,edges,faces])
		inputs = zip(vertices, edges, faces)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, tol))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyByGeometryNew)

def unregister():
	bpy.utils.unregister_class(SvTopologyByGeometryNew)

