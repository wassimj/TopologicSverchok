import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
#from sverchok.core.socket_data import SvGetSocketInfo

from . import Replication
import numpy as np
import pandas as pd
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
	graphs_file_path, edges_file_path, nodes_file_path, graph_id_header, graph_label_header, num_nodes_header, src_header, dst_header, node_label_header, node_attr_key, categories, bidirectional = item

	graphs = pd.read_csv(graphs_file_path)
	edges = pd.read_csv(edges_file_path)
	nodes = pd.read_csv(nodes_file_path)
	dgl_graphs = []
	labels = []

	# Create a graph for each graph ID from the edges table.
	# First process the graphs table into two dictionaries with graph IDs as keys.
	# The label and number of nodes are values.
	label_dict = {}
	num_nodes_dict = {}
	for _, row in graphs.iterrows():
		label_dict[row[graph_id_header]] = row[graph_label_header]
		num_nodes_dict[row[graph_id_header]] = row[num_nodes_header]
	# For the edges, first group the table by graph IDs.
	edges_group = edges.groupby(graph_id_header)
	# For the nodes, first group the table by graph IDs.
	nodes_group = nodes.groupby(graph_id_header)
	# For each graph ID...
	for graph_id in edges_group.groups:
		graph_dict = {}
		graph_dict[src_header] = []
		graph_dict[dst_header] = []
		graph_dict[node_label_header] = {}
		graph_dict["node_features"] = []
		num_nodes = num_nodes_dict[graph_id]
		graph_label = label_dict[graph_id]
		labels.append(graph_label)

		# Find the edges as well as the number of nodes and its label.
		edges_of_id = edges_group.get_group(graph_id)
		src = edges_of_id[src_header].to_numpy()
		dst = edges_of_id[dst_header].to_numpy()

		# Find the nodes and their labels and features
		nodes_of_id = nodes_group.get_group(graph_id)
		node_labels = nodes_of_id[node_label_header]
		#graph_dict["node_labels"][graph_id] = node_labels

		for node_label in node_labels:
			graph_dict["node_features"].append(torch.tensor(oneHotEncode(node_label, categories)))
		# Create a graph and add it to the list of graphs and labels.
		dgl_graph = dgl.graph((src, dst), num_nodes=num_nodes)
		# Setting the node features as node_attr_key using onehotencoding of node_label
		dgl_graph.ndata[node_attr_key] = torch.stack(graph_dict["node_features"])
		if bidirectional:
			dgl_graph = dgl.add_reverse_edges(dgl_graph)		
		dgl_graphs.append(dgl_graph)
	return [dgl_graphs, labels]

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDGLGraphByImportedCSV(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a DGLGraph from the input CSV files
	"""
	bl_idname = 'SvDGLGraphByImportedCSV'
	bl_label = 'DGL.DGLGraphByImportedCSV'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	GraphsFilePathProp: StringProperty(name="Graphs File Path", description="The file path to the Graphs CSV file", update=updateNode)
	EdgesFilePathProp: StringProperty(name="Edges File Path", description="The file path to the Edges CSV file", update=updateNode)
	NodesFilePathProp: StringProperty(name="Nodes File Path", description="The file path to the Nodes CSV file", update=updateNode)
	GraphIDHeaderProp: StringProperty(name="Graph ID Header", default="graph_id", description="The header title used for the graph ID column (Default: graph_id)", update=updateNode)
	GraphLabelHeaderProp: StringProperty(name="Graph Label Header", default="label", description="The header title used for the Graph label column (Default: label)", update=updateNode)
	GraphNumNodesHeaderProp: StringProperty(name="Graph Num Nodes Header", default="num_nodes", description="The header title used for the Graph Number of Nodes column (Default: num_nodes)", update=updateNode)
	EdgeSrcHeaderProp: StringProperty(name="Edge Src Header", default="src", description="The header title used for the Edge src column (Default: src)", update=updateNode)
	EdgeDstHeaderProp: StringProperty(name="Edge Dst Header", default="dst", description="The header title used for the Edge dst column (Default: dst)", update=updateNode)
	NodeLabelHeaderProp: StringProperty(name="Node Label Header", default="label", description="The header title used for the Node label column (Default: label)", update=updateNode)
	NodeAttrKeyProp: StringProperty(name="Node Attr Key", default="node_attr", description="The node attribute key to use (Default: node_attr)", update=updateNode)
	BidirectionalProp: BoolProperty(name="Bidirectional", default=True, update=updateNode)

	def sv_init(self, context):
		self.width = 300
		self.inputs.new('SvStringsSocket', 'Graphs File Path').prop_name = 'GraphsFilePathProp'
		self.inputs.new('SvStringsSocket', 'Edges File Path').prop_name = 'EdgesFilePathProp'
		self.inputs.new('SvStringsSocket', 'Nodes File Path').prop_name = 'NodesFilePathProp'
		self.inputs.new('SvStringsSocket', 'Graph ID Header').prop_name = 'GraphIDHeaderProp'
		self.inputs.new('SvStringsSocket', 'Graph Label Header').prop_name = 'GraphLabelHeaderProp'
		self.inputs.new('SvStringsSocket', 'Graph Num Nodes Header').prop_name = 'GraphNumNodesHeaderProp'
		self.inputs.new('SvStringsSocket', 'Edge Src Header').prop_name = 'EdgeSrcHeaderProp'
		self.inputs.new('SvStringsSocket', 'Edge Dst Header').prop_name = 'EdgeDstHeaderProp'
		self.inputs.new('SvStringsSocket', 'Node Label Header').prop_name = 'NodeLabelHeaderProp'
		self.inputs.new('SvStringsSocket', 'Node Attr Key').prop_name = 'NodeAttrKeyProp'
		self.inputs.new('SvStringsSocket', 'Node Categories')
		self.inputs.new('SvStringsSocket', 'Bidirectional').prop_name = 'BidirectionalProp'
		self.outputs.new('SvStringsSocket', 'DGL Graph')
		self.outputs.new('SvStringsSocket', 'Label')
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "SvDGLGraphByImportedCSV_draw_socket"

	def SvDGLGraphByImportedCSV_draw_socket(self, socket, context, layout):
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
		graphsFilePathList = self.inputs['Graphs File Path'].sv_get(deepcopy=False)
		edgesFilePathList = self.inputs['Edges File Path'].sv_get(deepcopy=False)
		nodesFilePathList = self.inputs['Nodes File Path'].sv_get(deepcopy=False)
		graphIDHeaderList = self.inputs['Graph ID Header'].sv_get(deepcopy=False)
		graphLabelHeaderList = self.inputs['Graph Label Header'].sv_get(deepcopy=False)
		graphNumNodesHeaderList = self.inputs['Graph Num Nodes Header'].sv_get(deepcopy=False)
		edgeSrcHeaderList = self.inputs['Edge Src Header'].sv_get(deepcopy=False)
		edgeDstHeaderList = self.inputs['Edge Dst Header'].sv_get(deepcopy=False)
		nodeLabelHeaderList = self.inputs['Node Label Header'].sv_get(deepcopy=False)
		nodeAttrKeyList = self.inputs['Node Attr Key'].sv_get(deepcopy=False)
		nodeCategoriesList = self.inputs['Node Categories'].sv_get(deepcopy=True)
		bidirectionalList = self.inputs['Bidirectional'].sv_get(deepcopy=True)

		graphsFilePathList = Replication.flatten(graphsFilePathList)
		edgesFilePathList = Replication.flatten(edgesFilePathList)
		nodesFilePathList = Replication.flatten(nodesFilePathList)
		graphIDHeaderList = Replication.flatten(graphIDHeaderList)
		graphLabelHeaderList = Replication.flatten(graphLabelHeaderList)
		graphNumNodesHeaderList = Replication.flatten(graphNumNodesHeaderList)
		edgeSrcHeaderList = Replication.flatten(edgeSrcHeaderList)
		edgeDstHeaderList = Replication.flatten(edgeDstHeaderList)
		nodeLabelHeaderList = Replication.flatten(nodeLabelHeaderList)
		nodeAttrKeyList = Replication.flatten(nodeAttrKeyList)
		#nodeCategoriesList = Replication.flatten(nodeCategoriesList)
		bidirectionalList = Replication.flatten(bidirectionalList)
		
		inputs = [graphsFilePathList,
		          edgesFilePathList,
				  nodesFilePathList,
				  graphIDHeaderList,
				  graphLabelHeaderList,
				  graphNumNodesHeaderList,
				  edgeSrcHeaderList,
				  edgeDstHeaderList,
				  nodeLabelHeaderList,
				  nodeAttrKeyList,
				  nodeCategoriesList,
				  bidirectionalList]

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
	bpy.utils.register_class(SvDGLGraphByImportedCSV)

def unregister():
	bpy.utils.unregister_class(SvDGLGraphByImportedCSV)
