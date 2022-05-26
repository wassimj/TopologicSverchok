import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication, DictionaryValueAtKey


def vertexIndex(vertex, vertices):
	for i in range(len(vertices)):
		if topologic.Topology.IsSame(vertex, vertices[i]):
			return i
	return None

def graphVertices(graph):
	vertices = []
	if graph:
		try:
			_ = graph.Vertices(vertices)
		except:
			print("ERROR: (Topologic>Graph.Vertices) operation failed.")
			vertices = None
	if vertices:
		return vertices
	else:
		return []

def adjacentVertices(graph, vertex):
	vertices = []
	_ = graph.AdjacentVertices(vertex, vertices)
	return list(vertices)

def processItem(item):
	graph, label, key, filepath, overwrite = item
	vertices = graphVertices(graph)
	outputString = str(len(vertices))+" "+str(label)+"\n"
	for j in range(len(vertices)):
		d = vertices[j].GetDictionary()
		vLabel = DictionaryValueAtKey.processItem([d, key])
		av = adjacentVertices(graph, vertices[j])
		outputString = outputString+str(vLabel)+" "+ str(len(av))+" "
		for k in range(len(av)):
			vi = vertexIndex(av[k], vertices)
			outputString = outputString+str(vi)+" "
		if j < len(vertices)-1:
			outputString = outputString+"\n"
	# Make sure the file extension is .txt
	ext = filepath[len(filepath)-4:len(filepath)]
	if ext.lower() != ".txt":
		filepath = filepath+".txt"
	f = None
	try:
		if overwrite == True:
			f = open(filepath, "w")
		else:
			f = open(filepath, "x") # Try to create a new File
	except:
		raise Exception("Error: Could not create a new file at the following location: "+filepath)
	if (f):
		f.write(outputString)
		f.close()	
		return True
	return False

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
	
class SvGraphExportToDGCNN(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Exports the input Graph to a text file compatible with DGCNN
	"""
	bl_idname = 'SvGraphExportToDGCNN'
	bl_label = 'Graph.ExportToDGCNN'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Label: StringProperty(name='Graph Label', default="0", update=updateNode)
	Key: StringProperty(name='Vertex Label Key', default="ID", update=updateNode)
	OverwriteProp: BoolProperty(name="Overwrite", default=True, update=updateNode)
	FilePath: StringProperty(name="File Path", default="", subtype="FILE_PATH")

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Graph Label').prop_name='Label'
		self.inputs.new('SvStringsSocket', 'Vertex Label Key').prop_name='Key'
		self.inputs.new('SvStringsSocket', 'File Path').prop_name='FilePath'
		self.inputs.new('SvStringsSocket', 'Overwrite File').prop_name = 'OverwriteProp'
		self.outputs.new('SvStringsSocket', 'Status')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Status'].sv_set([])
			return
		graphList = self.inputs['Graph'].sv_get(deepcopy=True)
		labelList = self.inputs['Graph Label'].sv_get(deepcopy=True)
		keyList = self.inputs['Vertex Label Key'].sv_get(deepcopy=True)
		graphList = Replication.flatten(graphList)
		labelList = Replication.flatten(labelList)
		keyList = Replication.flatten(keyList)
		filepathList = self.inputs['File Path'].sv_get(deepcopy=True)
		filepathList = Replication.flatten(filepathList)
		overwriteList = self.inputs['Overwrite File'].sv_get(deepcopy=False)
		overwriteList = Replication.flatten(overwriteList)
		inputs = [graphList, labelList, keyList, filepathList, overwriteList]
		if ((self.Replication) == "Default"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		if ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = Replication.repeat(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(Replication.interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Status'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvGraphExportToDGCNN)

def unregister():
	bpy.utils.unregister_class(SvGraphExportToDGCNN)
