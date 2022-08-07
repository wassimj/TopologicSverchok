import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
#from sverchok.core.socket_data import SvGetSocketInfo

import topologic
from . import Replication, DictionaryValueAtKey
import pandas as pd

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
	graph_list, \
    graph_label_list, \
    graphs_file_path, \
    edges_file_path, \
    nodes_file_path, \
    graph_id_header, \
    graph_label_header, \
    graph_num_nodes_header, \
    edge_src_header, \
    edge_dst_header, \
    node_label_header, \
    node_label_key, \
    default_node_label, \
    overwrite = item

	if not isinstance(graph_list, list):
		graph_list = [graph_list]
	for graph_index, graph in enumerate(graph_list):
		graph_label = graph_label_list[graph_index]
		# Export Graph Properties
		vertices = graphVertices(graph)
		graph_num_nodes = len(vertices)
		if overwrite == False:
			graphs = pd.read_csv(graphs_file_path)
			max_id = max(list(graphs[graph_id_header]))
			graph_id = max_id + graph_index + 1
		else:
			graph_id = graph_index
		data = [[graph_id], [graph_label], [graph_num_nodes]]
		data = Replication.iterate(data)
		data = Replication.transposeList(data)
		df = pd.DataFrame(data, columns= [graph_id_header, graph_label_header, graph_num_nodes_header])
		if overwrite == False:
			df.to_csv(graphs_file_path, mode='a', index = False, header=False)
		else:
			if graph_index == 0:
				df.to_csv(graphs_file_path, mode='w+', index = False, header=True)
			else:
				df.to_csv(graphs_file_path, mode='a', index = False, header=False)

		# Export Edge Properties
		edge_src = []
		edge_dst = []
		edge_graph_id = [] #Repetitive list of graph_id for each edge
		node_graph_id = [] #Repetitive list of graph_id for each vertex/node
		node_labels = []
		x_list = []
		y_list = []
		z_list = []
		node_data = []
		node_columns = [graph_id_header, node_label_header, "X", "Y", "Z"]
		# All keys should be the same for all vertices, so we can get them from the first vertex
		d = vertices[0].GetDictionary()
		keys = d.Keys()
		for key in keys:
			if key != node_label_key: #We have already saved that in its own column
				node_columns.append(key)
		for i, v in enumerate(vertices):
			# Might as well get the node labels since we are iterating through the vertices
			d = v.GetDictionary()
			vLabel = DictionaryValueAtKey.processItem([d, node_label_key])
			if not(vLabel):
				vLabel = default_node_label		
			single_node_data = [graph_id, vLabel, round(float(v.X()),5), round(float(v.Y()),5), round(float(v.Z()),5)]
			keys = d.Keys()
			for key in keys:
				if key != node_label_key and (key in node_columns):
					value = DictionaryValueAtKey.processItem([d, key])
					if not value:
						value = 'None'
					single_node_data.append(value)
			node_data.append(single_node_data)
			av = adjacentVertices(graph, v)
			for k in range(len(av)):
				vi = vertexIndex(av[k], vertices)
				edge_graph_id.append(graph_id)
				edge_src.append(i)
				edge_dst.append(vi)
		data = [edge_graph_id, edge_src, edge_dst]
		data = Replication.iterate(data)
		data = Replication.transposeList(data)
		df = pd.DataFrame(data, columns= [graph_id_header, edge_src_header, edge_dst_header])
		if overwrite == False:
			df.to_csv(edges_file_path, mode='a', index = False, header=False)
		else:
			if graph_index == 0:
				df.to_csv(edges_file_path, mode='w+', index = False, header=True)
			else:
				df.to_csv(edges_file_path, mode='a', index = False, header=False)

		# Export Node Properties
		df = pd.DataFrame(node_data, columns= node_columns)

		if overwrite == False:
			df.to_csv(nodes_file_path, mode='a', index = False, header=False)
		else:
			if graph_index == 0:
				df.to_csv(nodes_file_path, mode='w+', index = False, header=True)
			else:
				df.to_csv(nodes_file_path, mode='a', index = False, header=False)
	return True

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
	
class SvGraphExportToCSV(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Exports the input Graph to a CSV file compatible with DGL
	"""
	bl_idname = 'SvGraphExportToCSV'
	bl_label = 'Graph.ExportToCSV'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	GraphLabelProp: StringProperty(name='Graph Label', default="0", update=updateNode)
	GraphsFilePathProp: StringProperty(name="Graphs File Path", description="The file path to the Graphs CSV file", update=updateNode)
	GraphIDHeaderProp: StringProperty(name="Graph ID Header", default="graph_id", description="The header title used for the graph ID column (Default: graph_id)", update=updateNode)
	GraphLabelHeaderProp: StringProperty(name="Graph Label Header", default="label", description="The header title used for the Graph label column (Default: label)", update=updateNode)
	GraphNumNodesHeaderProp: StringProperty(name="Graph Num Nodes Header", default="num_nodes", description="The header title used for the Graph Number of Nodes column (Default: num_nodes)", update=updateNode)

	EdgesFilePathProp: StringProperty(name="Edges File Path", description="The file path to the Edges CSV file", update=updateNode)
	EdgeSrcHeaderProp: StringProperty(name="Edge Src Header", default="src", description="The header title used for the Edge src column (Default: src)", update=updateNode)
	EdgeDstHeaderProp: StringProperty(name="Edge Dst Header", default="dst", description="The header title used for the Edge dst column (Default: dst)", update=updateNode)

	NodesFilePathProp: StringProperty(name="Nodes File Path", description="The file path to the Nodes CSV file", update=updateNode)
	NodeLabelHeaderProp: StringProperty(name="Node Label Header", default="label", description="The header title used for the Node label column (Default: label)", update=updateNode)
	NodeAttrKeyProp: StringProperty(name="Node Attr Key", default="node_attr", description="The node attribute key to use (Default: node_attr)", update=updateNode)
	NodeKeyProp: StringProperty(name='Node Label Key', description="The dictionary key that holds the Vertex label", default="ID", update=updateNode)
	DefaultNodeLabelProp: IntProperty(name="Default Node Label", description="The default node label to save if none is found", default=0, update=updateNode)

	OverwriteProp: BoolProperty(name="Overwrite", default=True, update=updateNode)


	FilePath: StringProperty(name="File Path", default="", subtype="FILE_PATH")

	def sv_init(self, context):
		self.width = 300
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Graph Label').prop_name='GraphLabelProp'
		self.inputs.new('SvFilePathSocket', 'Graphs File Path').prop_name = 'GraphsFilePathProp'
		self.inputs.new('SvFilePathSocket', 'Edges File Path').prop_name = 'EdgesFilePathProp'
		self.inputs.new('SvFilePathSocket', 'Nodes File Path').prop_name = 'NodesFilePathProp'

		self.inputs.new('SvStringsSocket', 'Graph ID Header').prop_name = 'GraphIDHeaderProp'
		self.inputs.new('SvStringsSocket', 'Graph Label Header').prop_name = 'GraphLabelHeaderProp'
		self.inputs.new('SvStringsSocket', 'Graph Num Nodes Header').prop_name = 'GraphNumNodesHeaderProp'

		self.inputs.new('SvStringsSocket', 'Edge Src Header').prop_name = 'EdgeSrcHeaderProp'
		self.inputs.new('SvStringsSocket', 'Edge Dst Header').prop_name = 'EdgeDstHeaderProp'

		self.inputs.new('SvStringsSocket', 'Node Label Header').prop_name = 'NodeLabelHeaderProp'
		self.inputs.new('SvStringsSocket', 'Node Label Key').prop_name='NodeKeyProp'
		self.inputs.new('SvStringsSocket', 'Default Node Label').prop_name='DefaultNodeLabelProp'

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

		graphsFilePathList = self.inputs['Graphs File Path'].sv_get(deepcopy=False)
		edgesFilePathList = self.inputs['Edges File Path'].sv_get(deepcopy=False)
		nodesFilePathList = self.inputs['Nodes File Path'].sv_get(deepcopy=False)

		graphIDHeaderList = self.inputs['Graph ID Header'].sv_get(deepcopy=False)
		graphLabelHeaderList = self.inputs['Graph Label Header'].sv_get(deepcopy=False)
		graphNumNodesHeaderList = self.inputs['Graph Num Nodes Header'].sv_get(deepcopy=False)

		edgeSrcHeaderList = self.inputs['Edge Src Header'].sv_get(deepcopy=False)
		edgeDstHeaderList = self.inputs['Edge Dst Header'].sv_get(deepcopy=False)

		nodeLabelHeaderList = self.inputs['Node Label Header'].sv_get(deepcopy=False)
		nodeLabelKeyList = self.inputs['Node Label Key'].sv_get(deepcopy=False)
		defaultNodeLabelList = self.inputs['Default Node Label'].sv_get(deepcopy=False)

		overwriteList = self.inputs['Overwrite File'].sv_get(deepcopy=False)

		#graphList = Replication.flatten(graphList)
		#graphLabelList = Replication.flatten(graphLabelList)

		graphsFilePathList = Replication.flatten(graphsFilePathList)
		edgesFilePathList = Replication.flatten(edgesFilePathList)
		nodesFilePathList = Replication.flatten(nodesFilePathList)

		graphIDHeaderList = Replication.flatten(graphIDHeaderList)
		graphLabelHeaderList = Replication.flatten(graphLabelHeaderList)
		graphNumNodesHeaderList = Replication.flatten(graphNumNodesHeaderList)

		edgeSrcHeaderList = Replication.flatten(edgeSrcHeaderList)
		edgeDstHeaderList = Replication.flatten(edgeDstHeaderList)

		nodeLabelHeaderList = Replication.flatten(nodeLabelHeaderList)
		nodeLabelKeyList = Replication.flatten(nodeLabelKeyList)
		defaultNodeLabelList = Replication.flatten(defaultNodeLabelList)

		overwriteList = Replication.flatten(overwriteList)

		inputs = [graphList,
		          graphLabelList,
				  graphsFilePathList,
				  edgesFilePathList,
				  nodesFilePathList,
				  graphIDHeaderList,
				  graphLabelHeaderList,
				  graphNumNodesHeaderList,
				  edgeSrcHeaderList,
				  edgeDstHeaderList,
				  nodeLabelHeaderList,
				  nodeLabelKeyList,
				  defaultNodeLabelList,
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
	bpy.utils.register_class(SvGraphExportToCSV)

def unregister():
	bpy.utils.unregister_class(SvGraphExportToCSV)
