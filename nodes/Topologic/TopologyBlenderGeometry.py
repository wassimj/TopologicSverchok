import bpy
import bmesh
from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import uuid
from sverchok.utils.sv_mesh_utils import get_unique_faces

import topologic
from topologic import Topology, Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Graph, Dictionary, Attribute, VertexUtility, EdgeUtility, WireUtility, FaceUtility, ShellUtility, CellUtility, TopologyUtility

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

def repeat(list):
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

# From https://stackoverflow.com/questions/34432056/repeat-elements-of-list-between-each-other-until-we-reach-a-certain-length
def onestep(cur,y,base):
    # one step of the iteration
    if cur is not None:
        y.append(cur)
        base.append(cur)
    else:
        y.append(base[0])  # append is simplest, for now
        base = base[1:]+[base[0]]  # rotate
    return base

def iterate(list):
	maxLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		for i in range(len(anItem), maxLength):
			anItem.append(None)
		y=[]
		base=[]
		for cur in anItem:
			base = onestep(cur,y,base)
		returnList.append(y)
	return returnList

def trim(list):
	minLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength < minLength:
			minLength = newLength
	for anItem in list:
		anItem = anItem[:minLength]
		returnList.append(anItem)
	return returnList

# Adapted from https://stackoverflow.com/questions/533905/get-the-cartesian-product-of-a-series-of-lists
def interlace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in interlace(ar_list[1:]):
                yield [a,]+prod

def transposeList(l):
	length = len(l[0])
	returnList = []
	for i in range(length):
		tempRow = []
		for j in range(len(l)):
			tempRow.append(l[j][i])
		returnList.append(tempRow)
	return returnList

def getSubTopologies(topology, subTopologyClass):
	topologies = []
	if subTopologyClass == Vertex:
		_ = topology.Vertices(None, topologies)
	elif subTopologyClass == Edge:
		_ = topology.Edges(None, topologies)
	elif subTopologyClass == Wire:
		_ = topology.Wires(None, topologies)
	elif subTopologyClass == Face:
		_ = topology.Faces(None, topologies)
	elif subTopologyClass == Shell:
		_ = topology.Shells(None, topologies)
	elif subTopologyClass == Cell:
		_ = topology.Cells(None, topologies)
	elif subTopologyClass == CellComplex:
		_ = topology.CellComplexes(None, topologies)
	return topologies

def triangulate(faces):
	triangles = []
	for aFace in faces:
		ib = []
		_ = aFace.InternalBoundaries(ib)
		if len(ib) != 0:
			faceTriangles = []
			FaceUtility.Triangulate(aFace, 0.0, faceTriangles)
			for aFaceTriangle in faceTriangles:
				triangles.append(aFaceTriangle)
		else:
			triangles.append(aFace)
	return triangles

def processItem(item):
	topology, name, display = item
	# Delete any existing object with same name:
	#try:
		#bpy.data.objects.remove(bpy.data.objects[name])
	#except:
		#pass

	finalVertexList = []
	finalEdgeList = []
	finalFaceList = []
	vertices = []
	edges = []
	faces = []
	topVerts = []
	if (topology.Type() == 1): #input is a vertex, just add it and process it
		topVerts.append(topology)
	else:
		_ = topology.Vertices(None, topVerts)
	for aVertex in topVerts:
		try:
			vertices.index([aVertex.X(), aVertex.Y(), aVertex.Z()]) # Vertex already in list
		except:
			vertices.append([aVertex.X(), aVertex.Y(), aVertex.Z()]) # Vertex not in list, add it.
	topEdges = []
	if (topology.Type() == 2): #Input is an Edge, just add it and process it
		topEdges.append(topology)
	elif (topology.Type() > 2):
		_ = topology.Edges(None, topEdges)
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
	topFaces = []
	if (topology.Type() == 8): # Input is a Face, just add it and process it
		topFaces.append(topology)
	elif (topology.Type() > 8):
		_ = topology.Faces(None, topFaces)
	for aFace in topFaces:
		ib = []
		_ = aFace.InternalBoundaries(ib)
		if(len(ib) > 0):
			triFaces = []
			_ = FaceUtility.Triangulate(aFace, 0.0, triFaces)
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
			#wire = topologic.WireUtility.RemoveCollinearEdges(wire, 0.1) #This is an angle Tolerance
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
	try:
		bpy.ops.object.select_all(action='DESELECT')
		bpy.data.objects[name].select_set(True)
		bpy.ops.object.delete(use_global=True)
		bpy.data.objects.remove(bpy.data.objects[name])
	except:
		pass
	
	new_mesh = bpy.data.meshes.new(name+"_mesh")
	new_mesh.from_pydata(vertices, edges, faces)
	new_mesh.update()
	new_object = bpy.data.objects.new(name, new_mesh)


	view_layer = bpy.context.view_layer
	view_layer.active_layer_collection.collection.objects.link(new_object)
	if display:
		bpy.data.objects[name].hide_set(False)
	else:
		bpy.data.objects[name].hide_set(True)
	return new_object

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvTopologyBlenderGeometry(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Converts the input Topology into a blender geometry
	"""
	bl_idname = 'SvTopologyBlenderGeometry'
	bl_label = 'Topology.BlenderGeometry'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Name: StringProperty(name='Name', default="TopologicObject", update=updateNode)
	Display: BoolProperty(name="Display", default=False, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Name').prop_name='Name'
		self.inputs.new('SvStringsSocket', 'Display').prop_name='Display'
		self.outputs.new('SvVerticesSocket', 'Object')

	def process(self):
		start = time.time()
		#if not any(socket.is_linked for socket in self.outputs):
			#return
		if not any(socket.is_linked for socket in self.inputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		topologyList = flatten(topologyList)
		nameList = self.inputs['Name'].sv_get(deepcopy=True)
		nameList = flatten(nameList)
		displayList = self.inputs['Display'].sv_get(deepcopy=True)
		displayList = flatten(displayList)
		inputs = [topologyList, nameList, displayList]
		if ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Default" or (self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Object'].sv_set(outputs)
		end = time.time()
		print("Topology.BlenderGeometry Operation consumed "+str(round(end - start,2)*1000)+" ms")

def register():
	bpy.utils.register_class(SvTopologyBlenderGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyBlenderGeometry)

