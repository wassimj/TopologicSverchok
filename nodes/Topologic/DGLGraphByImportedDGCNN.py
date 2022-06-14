import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from . import Replication
import numpy as np
import torch
import dgl

def oneHotEncode(item, categories):
	if (item in categories) == False:
		raise Exception("Error: DGLGraph - One Hot Encoding - Node Label not in categories")
	returnList = []
	for i in range(len(categories)):
		if item == categories[i]:
			returnList.append(1)
		else:
			returnList.append(0)
	return returnList

def processItem(item):
	file_path, categories, bidirectional = item
	graphs = []
	labels = []
	file = open(file_path)
	if file:
		lines = file.readlines()
		n_graphs = int(lines[0])
		index = 1
		for i in range(n_graphs):
			graph_dict = {}
			graph_dict["src"] = []
			graph_dict["dst"] = []
			graph_dict["node_labels"] = {}
			graph_dict["node_features"] = []
			line = lines[index].split()
			n_nodes = int(line[0])
			graph_dict["num_nodes"] = n_nodes
			graph_label = int(line[1])
			labels.append(graph_label)
			index+=1
			for j in range(n_nodes):
				line = lines[index+j].split()
				node_label = int(line[0])
				graph_dict["node_labels"][j] = node_label
				graph_dict["node_features"].append(torch.tensor(oneHotEncode(node_label, categories)))
				adj_vertices = line[2:]
				for adj_vertex in adj_vertices:
					graph_dict["src"].append(j)
					graph_dict["dst"].append(int(adj_vertex))

			# Create DDGL graph
			src = np.array(graph_dict["src"])
			dst = np.array(graph_dict["dst"])
			# Create a graph
			dgl_graph = dgl.graph((src, dst), num_nodes=graph_dict["num_nodes"])
			# Setting the node features as 'node_attr' using onehotencoding of vlabel
			dgl_graph.ndata['node_attr'] = torch.stack(graph_dict["node_features"])
			if bidirectional:
				dgl_graph = dgl.add_reverse_edges(dgl_graph)		
			graphs.append(dgl_graph)
			index+=n_nodes
		file.close()
	return [graphs, labels]

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDGLGraphByImportedDGCNN(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a DGLGraph from the input DGCNN file
	"""
	bl_idname = 'SvDGLGraphByImportedDGCNN'
	bl_label = 'DGL.DGLGraphByImportedDGCNN'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	BidirectionalProp: BoolProperty(name="Bidirectional", default=True, update=updateNode)
	FilePathProp: StringProperty(name="File Path", description="The file path to the DGCNN file", update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvFilePathSocket', 'File Path').prop_name = 'FilePathProp'
		self.inputs.new('SvStringsSocket', 'Node Categories')
		self.inputs.new('SvStringsSocket', 'Bidirectional').prop_name = 'BidirectionalProp'
		self.outputs.new('SvStringsSocket', 'DGL Graph')
		self.outputs.new('SvStringsSocket', 'Label')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		filePathList = self.inputs['File Path'].sv_get(deepcopy=False)
		categoriesList = self.inputs['Node Categories'].sv_get(deepcopy=True)
		bidirectionalList = self.inputs['Bidirectional'].sv_get(deepcopy=True)
		filePathList = Replication.flatten(filePathList)
		bidirectionalList = Replication.flatten(bidirectionalList)
		
		inputs = [filePathList, categoriesList, bidirectionalList]
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
		graphs = []
		labels = []
		for anInput in inputs:
			graph, label = processItem(anInput)
			graphs.append(graph)
			labels.append(label)
		self.outputs['DGL Graph'].sv_set(graphs)
		self.outputs['Label'].sv_set(labels)

def register():
	bpy.utils.register_class(SvDGLGraphByImportedDGCNN)

def unregister():
	bpy.utils.unregister_class(SvDGLGraphByImportedDGCNN)
