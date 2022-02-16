import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, FloatVectorProperty, EnumProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last
from sverchok.utils.nodes_mixins.generating_objects import SvMeshData, SvViewerNode
from sverchok.utils.handle_blender_data import correct_collection_length
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
import sverchok.utils.meshes

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph, Dictionary
from itertools import cycle
import uuid
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

def topologyByFaces(faces, tolerance, outputMode):
	output = None
	if len(faces) == 1:
		return faces[0]
	if outputMode == "Cell":
		output = Cell.ByFaces(faces, tolerance)
		if output:
			return output
		else:
			raise Exception("Error: Could not create a Cell.")
	if outputMode == "CellComplex":
		output = CellComplex.ByFaces(faces, tolerance)
		if output:
			return output
		else:
			raise Exception("Error: Could not create a CellComplex.")
	if outputMode == "Shell":
		output = Shell.ByFaces(faces, tolerance)
		if output:
			return output
		else:
			raise Exception("Error: Could not create a Shell.")
	if outputMode == "Default":
		output = Cluster.ByTopologies(faces)
	if output:
		if output:
			return output
	return output

def topologyByEdges(edges):
	output = None
	if len(edges) == 1:
		return edges[0]
	output = Cluster.ByTopologies(edges)
	output = output.SelfMerge()
	return output

def getObjectKeysValues(bObject):
	keys = []
	values = []
	bad_obj_types = ['CAMERA','LAMP','ARMATURE']
	if bObject.type not in bad_obj_types:
		if len(bObject.keys()) > 1:
			# First item is _RNA_UI
			for K in bObject.keys():
				if K not in '_RNA_UI' and K not in 'BIMObjectProperties':
					keys.append(K)
					values.append(bObject[K])
	return [keys, values]

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("DictionaryByKeysValues - Keys and Values do not have the same length")
	stl_keys = []
	stl_values = []
	for i in range(len(keys)):
		if isinstance(keys[i], str):
			stl_keys.append(keys[i])
		else:
			stl_keys.append(str(keys[i]))
		if isinstance(values[i], list) and len(values[i]) == 1:
			value = values[i][0]
		else:
			value = values[i]
		if isinstance(value, bool):
			if value == False:
				stl_values.append(topologic.IntAttribute(0))
			else:
				stl_values.append(topologic.IntAttribute(1))
		elif isinstance(value, int):
			stl_values.append(topologic.IntAttribute(value))
		elif isinstance(value, float):
			stl_values.append(topologic.DoubleAttribute(value))
		elif isinstance(value, str):
			stl_values.append(topologic.StringAttribute(value))
		elif isinstance(value, list):
			l = []
			for v in value:
				if isinstance(v, bool):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, int):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, float):
					l.append(topologic.DoubleAttribute(v))
				elif isinstance(v, str):
					l.append(topologic.StringAttribute(v))
			stl_values.append(topologic.ListAttribute(l))
		else:
			raise Exception("Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
	myDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
	return myDict

def convertFaces(faces):
	returnList = []
	for aFace in faces:
		tempFace = []
		for v in aFace.vertices:
			tempFace.append(v)
		returnList.append(tempFace)
	return returnList
	
def processItem(item, tol, outputMode):
	returnTopology = None
	bObject, matrix, color, id, name  = item
	matrix = item[1]
	if matrix == "":
		matrix = bObject.matrix_world
	msh = bObject.data
	vertices = list(msh.vertices)
	edges = list(msh.edges)
	faces = convertFaces(list(msh.polygons))
	topVerts = []
	topEdges = []
	topFaces = []
	if len(vertices) > 0:
		vertices = [matrix @ vertex.co for vertex in vertices]
		for aVertex in vertices:
			v = Vertex.ByCoordinates(aVertex[0], aVertex[1], aVertex[2])
			topVerts.append(v)
	else:
		return None
	if len(faces) > 0:
		for aFace in faces:
			faceEdges = edgesByVertices(aFace, topVerts)
			faceWire = Wire.ByEdges(faceEdges)
			topFace = Face.ByExternalBoundary(faceWire)
			topFaces.append(topFace)
		returnTopology = topologyByFaces(topFaces, tol, outputMode)
	elif len(edges) > 0:
		for anEdge in edges:
			topEdge = Edge.ByStartVertexEndVertex(topVerts[anEdge[0]], topVerts[anEdge[1]])
			topEdges.append(topEdge)
		returnTopology = topologyByEdges(topEdges)
	else:
		returnTopology = Cluster.ByTopologies(topVerts)
	if returnTopology:
		keys = []
		values = []
		keys.append("color")
		keys.append("id")
		keys.append("name")
		keys.append("type")
		if color:
			if isinstance(color, tuple):
				color = list(color)
			elif isinstance(color, list):
				if isinstance(color[0], tuple):
					color = list(color[0])
			print(color)
			values.append(color)
		else:
			values.append(list(bObject.color))
		if id:
			values.append(id)
		else:
			values.append(str(uuid.uuid4()))
		print("Name", name)
		print("bObject.name", bObject.name)
		if name != "":
			values.append(name)
		elif bObject.name != "":
			values.append(bObject.name)
		else:
			values.append("None")
		values.append(returnTopology.GetTypeAsString())
		topDict = processKeysValues(keys, values)
		_ = returnTopology.SetDictionary(topDict)
	return returnTopology

def processVEF(item, tol, outputMode):
	vertices, edges, faces, color, id, name = item
	returnTopology = None
	if len(vertices) > 0:
		topVerts = []
		for aVertex in vertices:
			v = Vertex.ByCoordinates(aVertex[0], aVertex[1], aVertex[2])
			topVerts.append(v)
	else:
		return None
	if len(faces) > 0:
		topFaces = []
		for aFace in faces:
			faceEdges = edgesByVertices(aFace, topVerts)
			faceWire = Wire.ByEdges(faceEdges)
			topFace = Face.ByExternalBoundary(faceWire)
			topFaces.append(topFace)
		returnTopology = topologyByFaces(topFaces, tol, outputMode)
	elif len(edges) > 0:
		topEdges = []
		for anEdge in edges:
			topEdge = Edge.ByStartVertexEndVertex(topVerts[anEdge[0]], topVerts[anEdge[1]])
			topEdges.append(topEdge)
		returnTopology = topologyByEdges(topEdges)
	else:
		returnTopology = Cluster.ByTopologies(topVerts)
	if returnTopology:
		keys = []
		values = []
		keys.append("color")
		keys.append("id")
		keys.append("name")
		keys.append("type")
		if color:
			if isinstance(color, tuple):
				color = list(color)
			elif isinstance(color, list):
				if isinstance(color[0], tuple):
					color = list(color[0])
			print(color)
			values.append(color)
		else:
			values.append([1.0,1.0,1.0,1.0])
		if id:
			values.append(id)
		else:
			values.append(str(uuid.uuid4()))
		if name:
			values.append(name)
		else:
			values.append("None")
		values.append(returnTopology.GetTypeAsString())
		topDict = processKeysValues(keys, values)
		_ = returnTopology.SetDictionary(topDict)
	return returnTopology

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
input_items = [("Object", "Object", "", 1),("Vertex/Edge/Face", "Vertex/Edge/Face", "", 2)]
output_items = [("Default", "Default", "", 1),("CellComplex", "CellComplex", "", 2),("Cell", "Cell", "", 3), ("Shell", "Shell", "", 4)]

def update_sockets(self, context):
	# hide all input sockets
	self.inputs['Object'].hide_safe = True
	self.inputs['Matrix'].hide_safe = True
	self.inputs['Vertices'].hide_safe = True
	self.inputs['Edges'].hide_safe = True
	self.inputs['Faces'].hide_safe = True
	self.inputs['Name'].hide_safe = False
	self.inputs['Color'].hide_safe = False
	self.inputs['ID'].hide_safe = False

	if self.inputMode == "Object":
		self.inputs['Object'].hide_safe = False
		self.inputs['Matrix'].hide_safe = False
	else:
		self.inputs['Vertices'].hide_safe = False
		self.inputs['Edges'].hide_safe = False
		self.inputs['Faces'].hide_safe = False
	updateNode(self, context)

defaultID = str(uuid.uuid4())
class SvTopologyByGeometry(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology from the input geometry
	"""
	bl_idname = 'SvTopologyByGeometry'
	bl_label = 'Topology.ByGeometry'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	inputMode : EnumProperty(name='Input Mode', description='The input component format of the data', items=input_items, default="Object", update=update_sockets)
	outputMode : EnumProperty(name='Output Mode', description='The desired output format', items=output_items, default="Default", update=updateNode)
	Name: StringProperty(name="Name", default='None', update=updateNode)
	ID: StringProperty(name="ID", default=defaultID, update=updateNode)
	Color: FloatVectorProperty(update=updateNode, name='Color', default=(1.0, 1.0, 1.0, 1.0), size=4, min=0.0, max=1.0, subtype='COLOR')
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Object')
		self.inputs.new('SvStringsSocket', 'Vertices')
		self.inputs.new('SvStringsSocket', 'Edges')
		self.inputs.new('SvStringsSocket', 'Faces')
		self.inputs.new('SvMatrixSocket', 'Matrix')
		self.inputs.new('SvStringsSocket', 'Name').prop_name='Name'
		self.inputs.new('SvColorSocket', 'ID').prop_name='ID'
		self.inputs.new('SvColorSocket', 'Color').prop_name='Color'
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Topology')
		update_sockets(self, context)
	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "inputMode", expand=False, text="")
		layout.prop(self, "outputMode", expand=False, text="")


	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not (self.inputs['Matrix'].is_linked):
			matrixList = [""]
		else:
			matrixList = self.inputs['Matrix'].sv_get(deepcopy=True)
			matrixList = flatten(matrixList)

		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0][0]
		if self.inputMode == "Object":
			objectList = self.inputs['Object'].sv_get(deepcopy=True)
			objectList = flatten(objectList)
			colorList = self.inputs['Color'].sv_get(deepcopy=False)
			idList = self.inputs['ID'].sv_get(deepcopy=False)
			idList = flatten(idList)
			nameList = self.inputs['Name'].sv_get(deepcopy=False)
			nameList = flatten(nameList)
			inputs = [objectList, matrixList, colorList, idList, nameList]
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
				outputs.append(processItem(anInput, tol, self.outputMode))
		else:
			verticesList = self.inputs['Vertices'].sv_get(deepcopy=False, default=[[]])
			edgesList = self.inputs['Edges'].sv_get(deepcopy=False, default=[[]])
			facesList = self.inputs['Faces'].sv_get(deepcopy=False, default=[[]])
			nameList = self.inputs['Name'].sv_get(deepcopy=False)
			colorList = self.inputs['Color'].sv_get(deepcopy=False)
			idList = self.inputs['ID'].sv_get(deepcopy=False)
			idList = flatten(idList)
			nameList = flatten(nameList)
			inputs = [verticesList, edgesList, facesList, colorList, idList, nameList]
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
				outputs.append(processVEF(anInput, tol, self.outputMode))
		self.outputs['Topology'].sv_set(outputs)
		end = time.time()
		print("Topology.ByGeometry Operation consumed "+str(round(end - start,2)*1000)+" ms")

def register():
	bpy.utils.register_class(SvTopologyByGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyByGeometry)

