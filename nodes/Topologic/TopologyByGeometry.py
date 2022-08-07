import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, FloatVectorProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster
import uuid

from . import Replication
from . import DictionaryByKeysValues, TopologySelfMerge

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
        d = topologic.VertexUtility.Distance(v, aVertex)
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
		output = TopologySelfMerge.processItem(Cluster.ByTopologies(faces))
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
	if (outputMode == "Wire") and (len(edges) > 0):
		for anEdge in edges:
			topEdge = topologic.Edge.ByStartVertexEndVertex(topVerts[anEdge.vertices[0]], topVerts[anEdge.vertices[1]])
			topEdges.append(topEdge)
		returnTopology = topologyByEdges(topEdges)
	elif len(faces) > 0:
		for aFace in faces:
			faceEdges = edgesByVertices(aFace, topVerts)
			faceWire = Wire.ByEdges(faceEdges)
			topFace = Face.ByExternalBoundary(faceWire)
			topFaces.append(topFace)
		returnTopology = topologyByFaces(topFaces, tol, outputMode)
	elif len(edges) > 0:
		for anEdge in edges:
			topEdge = topologic.Edge.ByStartVertexEndVertex(topVerts[anEdge.vertices[0]], topVerts[anEdge.vertices[1]])
			topEdges.append(topEdge)
		returnTopology = topologyByEdges(topEdges)
	elif len(topVerts) > 0:
		returnTopology = Cluster.ByTopologies(topVerts)
	else:
		returnTopology = None
	if returnTopology:
		keys = []
		values = []
		for k, v in bObject.items():
			if isinstance(v, bool) or isinstance(v, int) or isinstance(v, float) or isinstance(v, str):
				keys.append(str(k))
				values.append(v)
		keys.append("TOPOLOGIC_color")
		keys.append("TOPOLOGIC_id")
		keys.append("TOPOLOGIC_name")
		keys.append("TOPOLOGIC_type")
		keys.append("TOPOLOGIC_length_unit")
		if color:
			if isinstance(color, tuple):
				color = list(color)
			elif isinstance(color, list):
				if isinstance(color[0], tuple):
					color = list(color[0])
			values.append(color)
		else:
			values.append(list(bObject.color))
		if id:
			values.append(id)
		else:
			values.append(str(uuid.uuid4()))
		if len(name) > 0 and name.lower() != 'none':
			values.append(name)
		elif len(bObject.name) > 0:
			values.append(bObject.name)
		else:
			values.append("Topologic_"+returnTopology.GetTypeAsString())
		values.append(returnTopology.GetTypeAsString())
		values.append(bpy.context.scene.unit_settings.length_unit)
		topDict = DictionaryByKeysValues.processKeysValues(keys, values)
		_ = returnTopology.SetDictionary(topDict)
	return returnTopology

def processVEF(item, tol, outputMode):
	vertices, edges, faces, color, id, name = item
	returnTopology = None
	topVerts = []
	topEdges = []
	topFaces = []
	if len(vertices) > 0:
		for aVertex in vertices:
			v = Vertex.ByCoordinates(aVertex[0], aVertex[1], aVertex[2])
			topVerts.append(v)
	else:
		return None
	if (outputMode == "Wire") and (len(edges) > 0):
		for anEdge in edges:
			topEdge = topologic.Edge.ByStartVertexEndVertex(topVerts[anEdge[0]], topVerts[anEdge[1]])
			topEdges.append(topEdge)
		returnTopology = topologyByEdges(topEdges)
	elif len(faces) > 0:
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
		keys.append("TOPOLOGIC_color")
		keys.append("TOPOLOGIC_id")
		keys.append("TOPOLOGIC_name")
		keys.append("TOPOLOGIC_type")
		keys.append("TOPOLOGIC_length_unit")
		if color:
			if isinstance(color, tuple):
				color = list(color)
			elif isinstance(color, list):
				if isinstance(color[0], tuple):
					color = list(color[0])
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
			values.append("Topologic_"+returnTopology.GetTypeAsString())
		values.append(returnTopology.GetTypeAsString())
		values.append(bpy.context.scene.unit_settings.length_unit)
		topDict = DictionaryByKeysValues.processKeysValues(keys, values)
		_ = returnTopology.SetDictionary(topDict)
	return returnTopology

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
input_items = [("Object", "Object", "", 1),("Mesh", "Mesh", "", 2)]
output_items = [("Default", "Default", "", 1),("CellComplex", "CellComplex", "", 2),("Cell", "Cell", "", 3), ("Shell", "Shell", "", 4), ("Wire", "Wire", "", 5)]

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
	bl_icon = 'SELECT_DIFFERENCE'

	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	inputMode : EnumProperty(name='Input Mode', description='The input component format of the data', items=input_items, default="Object", update=update_sockets)
	outputMode : EnumProperty(name='Output Mode', description='The desired output format', items=output_items, default="Default", update=updateNode)
	Name: StringProperty(name="Name", default='', update=updateNode)
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
		self.width = 200
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"
		update_sockets(self, context)

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Replication")
		split.row().prop(self, "Replication",text="")
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Input Mode")
		split.row().prop(self, "inputMode", expand=False, text="")
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Output Mode")
		split.row().prop(self, "outputMode", expand=False, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not (self.inputs['Matrix'].is_linked):
			matrixList = [""]
		else:
			matrixList = self.inputs['Matrix'].sv_get(deepcopy=True)
			matrixList = Replication.flatten(matrixList)

		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0][0]
		if self.inputMode == "Object":
			objectList = self.inputs['Object'].sv_get(deepcopy=True)
			objectList = Replication.flatten(objectList)
			colorList = self.inputs['Color'].sv_get(deepcopy=False)
			idList = self.inputs['ID'].sv_get(deepcopy=False)
			idList = Replication.flatten(idList)
			nameList = self.inputs['Name'].sv_get(deepcopy=False)
			nameList = Replication.flatten(nameList)
			inputs = [objectList, matrixList, colorList, idList, nameList]
			if ((self.Replication) == "Trim"):
				inputs = Replication.trim(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Default" or (self.Replication) == "Iterate"):
				inputs = Replication.iterate(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Repeat"):
				inputs = Replication.repeat(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Interlace"):
				inputs = list(Replication.interlace(inputs))
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
			idList = Replication.flatten(idList)
			nameList = Replication.flatten(nameList)
			inputs = [verticesList, edgesList, facesList, colorList, idList, nameList]
			if ((self.Replication) == "Trim"):
				inputs = Replication.trim(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Default" or (self.Replication) == "Iterate"):
				inputs = Replication.iterate(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Repeat"):
				inputs = Replication.repeat(inputs)
				inputs = Replication.transposeList(inputs)
			elif ((self.Replication) == "Interlace"):
				inputs = list(Replication.interlace(inputs))
			outputs = []
			for anInput in inputs:
				outputs.append(processVEF(anInput, tol, self.outputMode))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyByGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyByGeometry)

