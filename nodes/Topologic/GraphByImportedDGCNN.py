import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from . import Replication, DictionaryByKeysValues, TopologySetDictionary
import random

def verticesByCoordinates(x_coords, y_coords):
	vertices = []
	for i in range(len(x_coords)):
		vertices.append(topologic.Vertex.ByCoordinates(x_coords[i], y_coords[i], 0))
	return vertices

def processItem(item):
	file_path, key = item
	graphs = []
	labels = []
	file = open(file_path)
	if file:
		lines = file.readlines()
		n_graphs = int(lines[0])
		index = 1
		for i in range(n_graphs):
			edges = []
			line = lines[index].split()
			n_nodes = int(line[0])
			graph_label = int(line[1])
			labels.append(graph_label)
			index+=1
			x_coordinates = random.sample(range(0, n_nodes), n_nodes)
			y_coordinates = random.sample(range(0, n_nodes), n_nodes)
			vertices = verticesByCoordinates(x_coordinates, y_coordinates)
			for j in range(n_nodes):
				line = lines[index+j].split()
				node_label = int(line[0])
				node_dict = DictionaryByKeysValues.processItem([[key], [node_label]])
				TopologySetDictionary.processItem([vertices[j], node_dict])
			for j in range(n_nodes):
				line = lines[index+j].split()
				sv = vertices[j]
				adj_vertices = line[2:]
				for adj_vertex in adj_vertices:
					ev = vertices[int(adj_vertex)]
					e = topologic.Edge.ByStartVertexEndVertex(sv, ev)
					edges.append(e)
			index+=n_nodes
			graphs.append(topologic.Graph.ByVerticesEdges(vertices, edges))
		file.close()
	return [graphs, labels]

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
	
class SvGraphByImportedDGCNN(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Graph from the input DGCNN file
	"""
	bl_idname = 'SvGraphByImportedDGCNN'
	bl_label = 'Graph.ByImportedDGCNN'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Key: StringProperty(name='Vertex Label Key', default="ID", update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvFilePathSocket', 'File Path')
		self.inputs.new('SvStringsSocket', 'Vertex Label Key').prop_name='Key'
		self.outputs.new('SvStringsSocket', 'Graph')
		self.outputs.new('SvStringsSocket', 'Label')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		filePathList = self.inputs['File Path'].sv_get(deepcopy=False)
		keyList = self.inputs['Vertex Label Key'].sv_get(deepcopy=True)
		filePathList = Replication.flatten(filePathList)
		keyList = Replication.flatten(keyList)
		
		inputs = [filePathList, keyList]
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
		self.outputs['Graph'].sv_set(graphs)
		self.outputs['Label'].sv_set(labels)

def register():
	bpy.utils.register_class(SvGraphByImportedDGCNN)

def unregister():
	bpy.utils.unregister_class(SvGraphByImportedDGCNN)
