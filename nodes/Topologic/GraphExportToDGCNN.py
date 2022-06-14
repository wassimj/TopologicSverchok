import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
#from sverchok.core.socket_data import SvGetSocketInfo

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
	graph, graph_label, key, default_vertex_label, filepath, overwrite = item
	vertices = graphVertices(graph)
	new_lines = []
	new_lines.append("\n"+str(len(vertices))+" "+str(graph_label))
	for j in range(len(vertices)):
		d = vertices[j].GetDictionary()
		vLabel = DictionaryValueAtKey.processItem([d, key])
		if not(vLabel):
			vLabel = default_vertex_label
		av = adjacentVertices(graph, vertices[j])
		line = "\n"+str(vLabel)+" "+ str(len(av))+" "
		for k in range(len(av)):
			vi = vertexIndex(av[k], vertices)
			line = line+str(vi)+" "
		new_lines.append(line)
	# Make sure the file extension is .txt
	ext = filepath[len(filepath)-4:len(filepath)]
	if ext.lower() != ".txt":
		filepath = filepath+".txt"
	old_lines = ["1"]
	if overwrite == False:
		with open(filepath) as f:
			old_lines = f.readlines()
			if len(old_lines):
				if old_lines[0] != "":
					old_lines[0] = str(int(old_lines[0])+1)+"\n"
			else:
				old_lines[0] = "1"
	lines = old_lines+new_lines
	with open(filepath, "w") as f:
		f.writelines(lines)
	return True

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
	KeyProp: StringProperty(name='Vertex Label Key', default="ID", update=updateNode)
	VertexLabelProp: IntProperty(name="Default Vertex Label", default=0, update=updateNode)
	OverwriteProp: BoolProperty(name="Overwrite", default=True, update=updateNode)
	FilePath: StringProperty(name="File Path", default="")

	def sv_init(self, context):
		self.width = 225
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Graph Label').prop_name='Label'
		self.inputs.new('SvStringsSocket', 'Vertex Label Key').prop_name='KeyProp'
		self.inputs.new('SvStringsSocket', 'Default Vertex Label').prop_name='VertexLabelProp'
		self.inputs.new('SvFilePathSocket', 'File Path').prop_name='FilePath'
		self.inputs.new('SvStringsSocket', 'Overwrite File').prop_name = 'OverwriteProp'
		self.outputs.new('SvStringsSocket', 'Status')
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "SvGraphExportToDGCNN_draw_socket"

	def SvGraphExportToDGCNN_draw_socket(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.6)
		#split.row().label(text=socket.name+ '. ' + SvGetSocketInfo(socket))
		split.row().label(text=socket.name + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Status'].sv_set([])
			return
		graphList = self.inputs['Graph'].sv_get(deepcopy=True)
		labelList = self.inputs['Graph Label'].sv_get(deepcopy=True)
		keyList = self.inputs['Vertex Label Key'].sv_get(deepcopy=True)
		defaultVertexLabelList = self.inputs['Default Vertex Label'].sv_get(deepcopy=True)
		graphList = Replication.flatten(graphList)
		labelList = Replication.flatten(labelList)
		keyList = Replication.flatten(keyList)
		defaultVertexLabelList = Replication.flatten(defaultVertexLabelList)
		filepathList = self.inputs['File Path'].sv_get(deepcopy=True)
		filepathList = Replication.flatten(filepathList)
		overwriteList = self.inputs['Overwrite File'].sv_get(deepcopy=False)
		overwriteList = Replication.flatten(overwriteList)
		inputs = [graphList, labelList, keyList, defaultVertexLabelList, filepathList, overwriteList]
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
