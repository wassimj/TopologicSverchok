import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
#from sverchok.core.socket_data import SvGetSocketInfo

import topologic
from . import Replication, DictionaryValueAtKey
import pandas as pd
import os
import math

def vertexIndex(vertex, vertices):
	for i in range(len(vertices)):
		if topologic.Topology.IsSame(vertex, vertices[i]):
			return i
	return None

def graphVertices(graph):
	import random
	vertices = []
	if graph:
		try:
			_ = graph.Vertices(vertices)
		except:
			print("ERROR: (Topologic>Graph.Vertices) operation failed.")
			vertices = None
	if vertices:
		return random.sample(vertices, len(vertices))
	else:
		return []

def adjacentVertices(graph, vertex):
	vertices = []
	_ = graph.AdjacentVertices(vertex, vertices)
	return list(vertices)

def processItem(item):
	graph_list, \
    graph_label_list, \
    graphs_folder_path, \
    node_label_key, \
	node_features_keys, \
    default_node_label, \
	edge_label_key, \
	edge_features_keys, \
    default_edge_label, \
    train_ratio, \
    test_ratio, \
    validate_ratio, \
    overwrite = item

	assert (train_ratio+test_ratio+validate_ratio > 0.99), "GraphExportToCSV_NC - Error: Train_Test_Validate ratios do not add up to 1."

	if not isinstance(graph_list, list):
		graph_list = [graph_list]
	print("GRAPH LIST", graph_list)
	for graph_index, graph in enumerate(graph_list):
		print("GRAPH INDEX", graph_index)
		graph_label = graph_label_list[graph_index]
		# Export Graph Properties
		vertices = graphVertices(graph)
		train_max = math.floor(float(len(vertices))*train_ratio)
		test_max = math.floor(float(len(vertices))*test_ratio)
		validate_max = len(vertices) - train_max - test_max
		graph_num_nodes = len(vertices)
		if overwrite == False:
			graphs = pd.read_csv(os.path.join(graphs_folder_path,"graphs.csv"))
			max_id = max(list(graphs["graph_id"]))
			graph_id = max_id + graph_index + 1
		else:
			graph_id = graph_index
		data = [[graph_id], [graph_label], [graph_num_nodes]]
		data = Replication.iterate(data)
		data = Replication.transposeList(data)
		df = pd.DataFrame(data, columns= ["graph_id", "label", "num_nodes"])
		if overwrite == False:
			df.to_csv(os.path.join(graphs_folder_path, "graphs.csv"), mode='a', index = False, header=False)
		else:
			if graph_index == 0:
				df.to_csv(os.path.join(graphs_folder_path, "graphs.csv"), mode='w+', index = False, header=True)
			else:
				df.to_csv(os.path.join(graphs_folder_path, "graphs.csv"), mode='a', index = False, header=False)

		# Export Edge Properties
		edge_graph_id = [] #Repetitive list of graph_id for each edge
		edge_src = []
		edge_dst = []
		edge_lab = []
		edge_feat = []
		node_graph_id = [] #Repetitive list of graph_id for each vertex/node
		node_labels = []
		x_list = []
		y_list = []
		z_list = []
		node_data = []
		node_columns = ["graph_id", "node_id","label", "train_mask","val_mask","test_mask","feat", "X", "Y", "Z"]
		# All keys should be the same for all vertices, so we can get them from the first vertex
		d = vertices[0].GetDictionary()
		'''
		keys = d.Keys()
		for key in keys:
			if key != node_label_key: #We have already saved that in its own column
				node_columns.append(key)
		'''
		train = 0
		test = 0
		validate = 0
		
		for i, v in enumerate(vertices):
			print("VERTEX I", i)
			if train < train_max:
				train_mask = True
				test_mask = False
				validate_mask = False
				train = train + 1
			elif test < test_max:
				train_mask = False
				test_mask = True
				validate_mask = False
				test = test + 1
			elif validate < validate_max:
				train_mask = False
				test_mask = False
				validate_mask = True
				validate = validate + 1
			else:
				train_mask = True
				test_mask = False
				validate_mask = False
				train = train + 1
			# Might as well get the node labels since we are iterating through the vertices
			d = v.GetDictionary()
			vLabel = DictionaryValueAtKey.processItem([d, node_label_key])
			if not(vLabel):
				vLabel = default_node_label
			# Might as well get the features since we are iterating through the vertices
			features = ""
			node_features_keys = Replication.flatten(node_features_keys)
			for node_feature_key in node_features_keys:
				if len(features) > 0:
					features = features + ","+ str(round(float(DictionaryValueAtKey.processItem([d, node_feature_key])),5))
				else:
					features = str(round(float(DictionaryValueAtKey.processItem([d, node_feature_key])),5))
			single_node_data = [graph_id, i, vLabel, train_mask, validate_mask, test_mask, features, round(float(v.X()),5), round(float(v.Y()),5), round(float(v.Z()),5)]
			'''
			keys = d.Keys()
			for key in keys:
				if key != node_label_key and (key in node_columns):
					value = DictionaryValueAtKey.processItem([d, key])
					if not value:
						value = 'None'
					single_node_data.append(value)
			'''
			node_data.append(single_node_data)
			av = adjacentVertices(graph, v)
			for k in range(len(av)):
				vi = vertexIndex(av[k], vertices)
				edge_graph_id.append(graph_id)
				edge_src.append(i)
				edge_dst.append(vi)
				edge = graph.Edge(v, av[k], 0.0001)
				ed = edge.GetDictionary()
				edge_label = DictionaryValueAtKey.processItem([d, edge_label_key])
				if not(edge_label):
					edge_label = default_edge_label
				edge_lab.append(edge_label)
				edge_features = ""
				edge_features_keys = Replication.flatten(edge_features_keys)
				for edge_feature_key in edge_features_keys:
					if len(edge_features) > 0:
						edge_features = edge_features + ","+ str(round(float(DictionaryValueAtKey.processItem([ed, edge_feature_key])),5))
					else:
						edge_features = str(round(float(DictionaryValueAtKey.processItem([ed, edge_feature_key])),5))
				edge_feat.append(edge_features)
		print("EDGE_GRAPH_ID",edge_graph_id)
		data = [edge_graph_id, edge_src, edge_dst, edge_lab, edge_feat]
		data = Replication.iterate(data)
		data = Replication.transposeList(data)
		df = pd.DataFrame(data, columns= ["graph_id", "src_id", "dst_id", "label", "feat"])
		if overwrite == False:
			df.to_csv(os.path.join(graphs_folder_path, "edges.csv"), mode='a', index = False, header=False)
		else:
			if graph_index == 0:
				df.to_csv(os.path.join(graphs_folder_path, "edges.csv"), mode='w+', index = False, header=True)
			else:
				df.to_csv(os.path.join(graphs_folder_path, "edges.csv"), mode='a', index = False, header=False)

		# Export Node Properties
		df = pd.DataFrame(node_data, columns= node_columns)

		if overwrite == False:
			df.to_csv(os.path.join(graphs_folder_path, "nodes.csv"), mode='a', index = False, header=False)
		else:
			if graph_index == 0:
				df.to_csv(os.path.join(graphs_folder_path, "nodes.csv"), mode='w+', index = False, header=True)
			else:
				df.to_csv(os.path.join(graphs_folder_path, "nodes.csv"), mode='a', index = False, header=False)
	# Write out the meta.yaml file
	yaml_file = open(os.path.join(graphs_folder_path,"meta.yaml"), "w")
	yaml_file.write('dataset_name: topologic_dataset\nedge_data:\n- file_name: edges.csv\nnode_data:\n- file_name: nodes.csv\ngraph_data:\n  file_name: graphs.csv')
	yaml_file.close()
	return True

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
	
class SvGraphExportToCSV_NC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Exports the input Graph to a CSV file compatible with DGL
	"""
	bl_idname = 'SvGraphExportToCSV_NC'
	bl_label = 'Graph.ExportToCSV_NC'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	GraphLabelProp: StringProperty(name='Graph Label', default="0", update=updateNode)
	GraphsFolderPathProp: StringProperty(name="Graphs Folder Path", description="The folder path to the Graphs CSV files", update=updateNode)
	NodeAttrKeyProp: StringProperty(name="Node Attr Key", default="node_attr", description="The node attribute key to use (Default: node_attr)", update=updateNode)
	NodeKeyProp: StringProperty(name='Node Label Key', description="The dictionary key that holds the Node label", default="ID", update=updateNode)
	NodeFeaturesKeysProp: StringProperty(name='Node Features Keys', description="A list of the dictionary keys that hold the Node features", update=updateNode)
	DefaultNodeLabelProp: IntProperty(name="Default Node Label", description="The default node label to save if none is found", default=0, update=updateNode)
	EdgeKeyProp: StringProperty(name='Edge Label Key', description="The dictionary key that holds the Edge label", default="ID", update=updateNode)
	EdgeFeaturesKeysProp: StringProperty(name='Edge Features Keys', description="A list of the dictionary keys that hold the Edge features", update=updateNode)
	DefaultEdgeLabelProp: IntProperty(name="Default Edge Label", description="The default edge label to save if none is found", default=0, update=updateNode)
	TrainRatioProp: FloatProperty(name="Train Ratio", description="The portion of data to be used for training", default=0.7, min=0.1, max=0.9, update=updateNode)
	TestRatioProp: FloatProperty(name="Test Ratio", description="The portion of data to be used for testing", default=0.2, min=0.1, max=0.9, update=updateNode)
	ValidateRatioProp: FloatProperty(name="Validate Ratio", description="The portion of data to be used for validation", default=0.1, min=0.1, max=0.9, update=updateNode)

	OverwriteProp: BoolProperty(name="Overwrite", default=True, update=updateNode)


	FilePath: StringProperty(name="File Path", default="", subtype="FILE_PATH")

	def sv_init(self, context):
		self.width = 300
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Graph Label').prop_name='GraphLabelProp'
		self.inputs.new('SvFilePathSocket', 'Graphs Folder Path').prop_name = 'GraphsFolderPathProp'

		self.inputs.new('SvStringsSocket', 'Node Label Key').prop_name='NodeKeyProp'
		self.inputs.new('SvStringsSocket', 'Node Features Keys').prop_name='NodeFeaturesKeysProp'
		self.inputs.new('SvStringsSocket', 'Default Node Label').prop_name='DefaultNodeLabelProp'

		self.inputs.new('SvStringsSocket', 'Edge Label Key').prop_name='EdgeKeyProp'
		self.inputs.new('SvStringsSocket', 'Edge Features Keys').prop_name='EdgeFeaturesKeysProp'
		self.inputs.new('SvStringsSocket', 'Default Edge Label').prop_name='DefaultEdgeLabelProp'

		self.inputs.new('SvStringsSocket', 'Train Ratio').prop_name='TrainRatioProp'
		self.inputs.new('SvStringsSocket', 'Test Ratio').prop_name='TestRatioProp'
		self.inputs.new('SvStringsSocket', 'Validate Ratio').prop_name='ValidateRatioProp'

		self.inputs.new('SvStringsSocket', 'Overwrite File').prop_name = 'OverwriteProp'

		self.outputs.new('SvStringsSocket', 'Status')

		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "SvGraphExportToCSV_draw_socket"

	def SvGraphExportToCSV_draw_socket(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.6)
		#split.row().label(text=socket.name+ '. ' + SvGetSocketInfo(socket))
		split.row().label(text=socket.name + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Status'].sv_set([])
			return

		graphList = self.inputs['Graph'].sv_get(deepcopy=False)
		graphLabelList = self.inputs['Graph Label'].sv_get(deepcopy=False)

		graphsFolderPathList = self.inputs['Graphs Folder Path'].sv_get(deepcopy=False)

		nodeLabelKeyList = self.inputs['Node Label Key'].sv_get(deepcopy=False)
		nodeFeaturesKeysList = self.inputs['Node Features Keys'].sv_get(deepcopy=False)
		defaultNodeLabelList = self.inputs['Default Node Label'].sv_get(deepcopy=False)

		edgeLabelKeyList = self.inputs['Edge Label Key'].sv_get(deepcopy=False)
		edgeFeaturesKeysList = self.inputs['Edge Features Keys'].sv_get(deepcopy=False)
		defaultEdgeLabelList = self.inputs['Default Edge Label'].sv_get(deepcopy=False)

		trainRatioList = self.inputs['Train Ratio'].sv_get(deepcopy=False)
		testRatioList = self.inputs['Test Ratio'].sv_get(deepcopy=False)
		validateRatioList = self.inputs['Validate Ratio'].sv_get(deepcopy=False)

		overwriteList = self.inputs['Overwrite File'].sv_get(deepcopy=False)

		graphsFolderPathList = Replication.flatten(graphsFolderPathList)

		nodeLabelKeyList = Replication.flatten(nodeLabelKeyList)
		defaultNodeLabelList = Replication.flatten(defaultNodeLabelList)

		edgeLabelKeyList = Replication.flatten(edgeLabelKeyList)
		defaultEdgeLabelList = Replication.flatten(defaultEdgeLabelList)

		trainRatioList = Replication.flatten(trainRatioList)
		testRatioList = Replication.flatten(testRatioList)
		validateRatioList = Replication.flatten(validateRatioList)

		overwriteList = Replication.flatten(overwriteList)

		inputs = [graphList,
		          graphLabelList,
				  graphsFolderPathList,
				  nodeLabelKeyList,
				  nodeFeaturesKeysList,
				  defaultNodeLabelList,
				  edgeLabelKeyList,
				  edgeFeaturesKeysList,
				  defaultEdgeLabelList,
				  trainRatioList,
				  testRatioList,
				  validateRatioList,
				  overwriteList]
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
	bpy.utils.register_class(SvGraphExportToCSV_NC)

def unregister():
	bpy.utils.unregister_class(SvGraphExportToCSV_NC)
