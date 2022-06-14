import sys
sys.path.append(r"D:\Anaconda3\envs\py310\Lib\site-packages")
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import dgl
from dgl.data import DGLDataset
import torch
import numpy as np

from . import Replication

samples = [("ENZYMES", "ENZYMES", "", 1),
           ("DD", "DD", "", 2),
           ("COLLAB", "COLLAB", "", 3),
           ("MUTAG", "MUTAG", "", 4)]

class GraphDGL(DGLDataset):
	def __init__(self, graphs, labels, node_attr_key):
		super().__init__(name='GraphDGL')
		self.graphs = graphs
		self.labels = torch.LongTensor(labels)
		self.node_attr_key = node_attr_key
		# as all graphs have same length of node features then we get dim_nfeats from first graph in the list
		self.dim_nfeats = graphs[0].ndata[node_attr_key].shape[1]
		#self.dim_nfeats = labels.shape[0]
        # to get the number of classes for graphs
		self.gclasses = len(set(labels))

	def __getitem__(self, i):
		return self.graphs[i], self.labels[i]

	def __len__(self):
		return len(self.graphs)

def processItem(item):
	sample = item
	dataset = dgl.data.TUDataset(sample)
	dgl_graphs, dgl_labels = zip(*[dataset[i] for i in range(len(dataset.graph_lists))])
	if sample == 'ENZYMES':
		node_attr_key = 'node_attr'
	elif sample == 'DD':
		node_attr_key = 'node_labels'
	elif sample == 'COLLAB':
		node_attr_key = '_ID'
	elif sample == 'MUTAG':
		node_attr_key = 'node_labels'
	else:
		raise NotImplementedError
	return GraphDGL(dgl_graphs, dgl_labels, node_attr_key)

class SvDGLDatasetBySamples(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a DGL Dataset by DGL Samples
	"""
	bl_idname = 'SvDGLDatasetBySamples'
	bl_label = 'DGL.DatasetBySamples'
	SamplesProp: EnumProperty(name="Samples", description="Choose a sample dataset", default="ENZYMES", items=samples, update=updateNode)

	def sv_init(self, context):
		self.width=200
		self.inputs.new('SvStringsSocket', 'Sample').prop_name="SamplesProp"
		self.outputs.new('SvStringsSocket', 'DGL Dataset')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		sampleList = self.inputs['Sample'].sv_get(deepcopy=True)
		sampleList = Replication.flatten(sampleList)
		outputs = []
		for anInput in sampleList:
			outputs.append(processItem(anInput))
		self.outputs['DGL Dataset'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDGLDatasetBySamples)

def unregister():
	bpy.utils.unregister_class(SvDGLDatasetBySamples)
