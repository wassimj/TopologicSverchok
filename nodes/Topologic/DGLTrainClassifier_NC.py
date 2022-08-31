import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from . import Replication

import dgl
import torch
import torch.nn as nn
import torch.nn.functional as F
import dgl.data

import random
from dgl.nn import GraphConv, SAGEConv

from . import DGLDatasetGraphs_NC

class GCN_GraphConv(nn.Module):
	def __init__(self, in_feats, h_feats, num_classes):
		super(GCN_GraphConv, self).__init__()
		self.list_of_layers = []
		if not isinstance(h_feats, list):
			h_feats = [h_feats]
		dim = [in_feats] + h_feats
		for i in range(1, len(dim)):
			self.list_of_layers.append(GraphConv(dim[i-1], dim[i]))
		self.list_of_layers = nn.ModuleList(self.list_of_layers)
		self.final = GraphConv(int(dim[-1]), int(num_classes))

	def forward(self, g, in_feat):
		h = in_feat.float()
		for i in range(len(self.list_of_layers)):
			h = self.list_of_layers[i](g, h)
			h = F.relu(h)
		h = self.final(g, h)
		return h

class GCN_SAGEConv(nn.Module):
	def __init__(self, in_feats, h_feats, num_classes):
		super(GCN_SAGEConv, self).__init__()
		self.list_of_layers = []
		if not isinstance(h_feats, list):
			h_feats = [h_feats]
		dim = [in_feats] + h_feats
		for i in range(1, len(dim)):
			self.list_of_layers.append(SAGEConv(in_feats=dim[i-1], out_feats=dim[i], aggregator_type='mean'))
		self.list_of_layers = nn.ModuleList(self.list_of_layers)
		self.final = dgl.nn.SAGEConv(
			in_feats=int(dim[-1]), out_feats=int(num_classes), aggregator_type='mean')

	def forward(self, g, in_feat):
		h = in_feat.float()
		for i in range(len(self.list_of_layers)):
			h = self.list_of_layers[i](g, h)
			h = F.relu(h)
		h = self.final(g, h)
		return h

def train(g, model, hparams):
	# Default optimizer
	optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
	if hparams.optimizer_str == "Adadelta":
		optimizer = torch.optim.Adadelta(model.parameters(), eps=hparams.eps, 
											lr=hparams.lr, rho=hparams.rho, weight_decay=hparams.weight_decay)
	elif hparams.optimizer_str == "Adagrad":
		optimizer = torch.optim.Adagrad(model.parameters(), eps=hparams.eps, 
											lr=hparams.lr, lr_decay=hparams.lr_decay, weight_decay=hparams.weight_decay)
	elif hparams.optimizer_str == "Adam":
		optimizer = torch.optim.Adam(model.parameters(), amsgrad=hparams.amsgrad, betas=hparams.betas, eps=hparams.eps, 
											lr=hparams.lr, maximize=hparams.maximize, weight_decay=hparams.weight_decay)
	best_val_acc = 0
	best_test_acc = 0

	features = g.ndata['feat']
	labels = g.ndata['label']
	train_mask = g.ndata['train_mask']
	val_mask = g.ndata['val_mask']
	test_mask = g.ndata['test_mask']
	for e in range(hparams.epochs):
		# Forward
		logits = model(g, features)

		# Compute prediction
		pred = logits.argmax(1)

		# Compute loss
		# Note that you should only compute the losses of the nodes in the training set.
		loss = F.cross_entropy(logits[train_mask], labels[train_mask])

		# Compute accuracy on training/validation/test
		train_acc = (pred[train_mask] == labels[train_mask]).float().mean()
		val_acc = (pred[val_mask] == labels[val_mask]).float().mean()
		test_acc = (pred[test_mask] == labels[test_mask]).float().mean()

		# Save the best validation accuracy and the corresponding test accuracy.
		if best_val_acc < val_acc:
			best_val_acc = val_acc
			best_test_acc = test_acc

		# Backward
		optimizer.zero_grad()
		loss.backward()
		optimizer.step()

		print('In epoch {}, loss: {:.3f}, train acc: {:.3f}, val acc: {:.3f} (best {:.3f}), test acc: {:.3f} (best {:.3f})'.format(
				e, loss, train_acc, val_acc, best_val_acc, test_acc, best_test_acc))
	return model

def processItem(item):
	hparams, dataset, numLabels = item
	graphs = DGLDatasetGraphs_NC.processItem(dataset)
	g = graphs[0]
	transform = dgl.AddReverse(copy_edata=True)
	g = transform(g)
	model = None
	if hparams.conv_layer_type == 'GraphConv':
			model = GCN_GraphConv(g.ndata['feat'].shape[1], hparams.hidden_layers, numLabels)
	elif hparams.conv_layer_type == 'SAGEConv':
		model = GCN_SAGEConv(g.ndata['feat'].shape[1], hparams.hidden_layers, numLabels)
	else:
		raise NotImplementedError
	trained_model = train(g, model, hparams)
	# Save the entire model
	if hparams.checkpoint_path is not None:
		torch.save(trained_model, hparams.checkpoint_path)
	return trained_model

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDGLTrainClassifier_NC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Trains a DGL Classifier for Node Classification
	"""
	
	bl_idname = 'SvDGLTrainClassifier_NC'
	bl_label = 'DGL.TrainClassifier_NC'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	HyperparametersProp: StringProperty(name="Hyperparameters", update=updateNode)
	NumLabels: IntProperty(name="Num Labels", default=5, min=1, update=updateNode)
	Sample: IntProperty(name="Sample", default=0, min=0, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Hyperparameters').prop_name="HyperparametersProp"
		self.inputs.new('SvStringsSocket', 'Dataset')
		self.inputs.new('SvStringsSocket', 'Num Labels')
		self.outputs.new('SvStringsSocket', 'Classifier')

	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Replication")
		split.row().prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		hyperparametersList = self.inputs['Hyperparameters'].sv_get(deepcopy=True)
		datasetList = self.inputs['Dataset'].sv_get(deepcopy=True)
		numLabelsList = self.inputs['Num Labels'].sv_get(deepcopy=True)
		hyperparametersList = Replication.flatten(hyperparametersList)
		datasetList = Replication.flatten(datasetList)
		numLabelsList = Replication.flatten(numLabelsList)
		inputs = [hyperparametersList, datasetList, numLabelsList]
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
		self.outputs['Classifier'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDGLTrainClassifier_NC)

def unregister():
	bpy.utils.unregister_class(SvDGLTrainClassifier_NC)
