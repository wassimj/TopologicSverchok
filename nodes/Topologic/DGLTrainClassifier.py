import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
#from sverchok.core.update_system import make_tree_from_nodes, do_update
from sverchok.core.update_system import UpdateTree
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
#from sverchok.core.socket_data import SvGetSocketInfo

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data.sampler import SubsetRandomSampler
from torch.utils.data import DataLoader, ConcatDataset
from sklearn.model_selection import KFold

import dgl
from dgl.dataloading import GraphDataLoader
from dgl.nn import GINConv, GraphConv, SAGEConv, TAGConv

import time
from datetime import datetime

import pandas as pd
import numpy as np

from . import Replication
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]


class GCN_Classic(nn.Module):
	def __init__(self, in_feats, h_feats, num_classes):
		"""

        Parameters
        ----------
        in_feats : int
            Input dimension in the form of integer
        h_feats : list
            List of hidden neurons for each hidden layer
        num_classes : int
            Number of output classes

        Returns
        -------
        None.

		"""
		super(GCN_Classic, self).__init__()
		assert isinstance(h_feats, list), "h_feats must be a list"
		h_feats = [x for x in h_feats if x is not None]
		assert len(h_feats) !=0, "h_feats is empty. unable to add hidden layers"
		self.list_of_layers = []
		dim = [in_feats] + h_feats
		for i in range(1, len(dim)):
			self.list_of_layers.append(GraphConv(dim[i-1], dim[i]))
		self.final = GraphConv(dim[-1], num_classes)

	def forward(self, g, in_feat):
		h = in_feat
		for i in range(len(self.list_of_layers)):
			h = self.list_of_layers[i](g, h)
			h = F.relu(h)
		h = self.final(g, h)
		g.ndata['h'] = h
		return dgl.mean_nodes(g, 'h')

class GCN_GINConv(nn.Module):
	def __init__(self, in_feats, h_feats, num_classes, pooling):
		super(GCN_GINConv, self).__init__()
		assert isinstance(h_feats, list), "h_feats must be a list"
		h_feats = [x for x in h_feats if x is not None]
		assert len(h_feats) !=0, "h_feats is empty. unable to add hidden layers"
		self.list_of_layers = []
		dim = [in_feats] + h_feats

		# Convolution (Hidden) Layers
		for i in range(1, len(dim)):
			lin = nn.Linear(dim[i-1], dim[i])
			self.list_of_layers.append(GINConv(lin, 'sum'))

		# Final Layer
		self.final = nn.Linear(dim[-1], num_classes)

		# Pooling layer
		if pooling == "AvgPooling":
			self.pooling_layer = dgl.nn.AvgPooling()
		elif pooling == "MaxPooling":
			self.pooling_layer = dgl.nn.MaxPooling()
		elif pooling == "SumPooling":
			self.pooling_layer = dgl.nn.SumPooling()
		else:
			raise NotImplementedError

	def forward(self, g, in_feat):
		h = in_feat
		# Generate node features
		for i in range(len(self.list_of_layers)): # Aim for 2 about 3 layers
			h = self.list_of_layers[i](g, h)
			h = F.relu(h)
		# h will now be matrix of dimension num_nodes by h_feats[-1]
		h = self.final(h)
		g.ndata['h'] = h
		# Go from node level features to graph level features by pooling
		h = self.pooling_layer(g, h)
		# h will now be vector of dimension num_classes
		return h

class GCN_GraphConv(nn.Module):
	def __init__(self, in_feats, h_feats, num_classes, pooling):
		super(GCN_GraphConv, self).__init__()
		assert isinstance(h_feats, list), "h_feats must be a list"
		h_feats = [x for x in h_feats if x is not None]
		assert len(h_feats) !=0, "h_feats is empty. unable to add hidden layers"
		self.list_of_layers = []
		dim = [in_feats] + h_feats

		# Convolution (Hidden) Layers
		for i in range(1, len(dim)):
			self.list_of_layers.append(GraphConv(dim[i-1], dim[i]))

		# Final Layer
		# Followed example at: https://docs.dgl.ai/tutorials/blitz/5_graph_classification.html#sphx-glr-tutorials-blitz-5-graph-classification-py
		self.final = GraphConv(dim[-1], num_classes)

		# Pooling layer
		if pooling == "AvgPooling":
			self.pooling_layer = dgl.nn.AvgPooling()
		elif pooling == "MaxPooling":
			self.pooling_layer = dgl.nn.MaxPooling()
		elif pooling == "SumPooling":
			self.pooling_layer = dgl.nn.SumPooling()
		else:
			raise NotImplementedError

	def forward(self, g, in_feat):
		h = in_feat
		# Generate node features
		for i in range(len(self.list_of_layers)): # Aim for 2 about 3 layers
			h = self.list_of_layers[i](g, h)
			h = F.relu(h)
		# h will now be matrix of dimension num_nodes by h_feats[-1]
		h = self.final(g,h)
		g.ndata['h'] = h
		# Go from node level features to graph level features by pooling
		h = self.pooling_layer(g, h)
		# h will now be vector of dimension num_classes
		return h

class GCN_SAGEConv(nn.Module):
	def __init__(self, in_feats, h_feats, num_classes, pooling):
		super(GCN_SAGEConv, self).__init__()
		assert isinstance(h_feats, list), "h_feats must be a list"
		h_feats = [x for x in h_feats if x is not None]
		assert len(h_feats) !=0, "h_feats is empty. unable to add hidden layers"
		self.list_of_layers = []
		dim = [in_feats] + h_feats

		# Convolution (Hidden) Layers
		for i in range(1, len(dim)):
			self.list_of_layers.append(SAGEConv(dim[i-1], dim[i], aggregator_type='pool'))

		# Final Layer
		self.final = nn.Linear(dim[-1], num_classes)

		# Pooling layer
		if pooling == "AvgPooling":
			self.pooling_layer = dgl.nn.AvgPooling()
		elif pooling == "MaxPooling":
			self.pooling_layer = dgl.nn.MaxPooling()
		elif pooling == "SumPooling":
			self.pooling_layer = dgl.nn.SumPooling()
		else:
			raise NotImplementedError

	def forward(self, g, in_feat):
		h = in_feat
		# Generate node features
		for i in range(len(self.list_of_layers)): # Aim for 2 about 3 layers
			h = self.list_of_layers[i](g, h)
			h = F.relu(h)
		# h will now be matrix of dimension num_nodes by h_feats[-1]
		h = self.final(h)
		g.ndata['h'] = h
		# Go from node level features to graph level features by pooling
		h = self.pooling_layer(g, h)
		# h will now be vector of dimension num_classes
		return h

class GCN_TAGConv(nn.Module):
	def __init__(self, in_feats, h_feats, num_classes, pooling):
		super(GCN_TAGConv, self).__init__()
		assert isinstance(h_feats, list), "h_feats must be a list"
		h_feats = [x for x in h_feats if x is not None]
		assert len(h_feats) !=0, "h_feats is empty. unable to add hidden layers"
		self.list_of_layers = []
		dim = [in_feats] + h_feats

		# Convolution (Hidden) Layers
		for i in range(1, len(dim)):
			self.list_of_layers.append(TAGConv(dim[i-1], dim[i], k=2))

		# Final Layer
		self.final = nn.Linear(dim[-1], num_classes)

		# Pooling layer
		if pooling == "AvgPooling":
			self.pooling_layer = dgl.nn.AvgPooling()
		elif pooling == "MaxPooling":
			self.pooling_layer = dgl.nn.MaxPooling()
		elif pooling == "SumPooling":
			self.pooling_layer = dgl.nn.SumPooling()
		else:
			raise NotImplementedError

	def forward(self, g, in_feat):
		h = in_feat
		# Generate node features
		for i in range(len(self.list_of_layers)): # Aim for 2 about 3 layers
			h = self.list_of_layers[i](g, h)
			h = F.relu(h)
		# h will now be matrix of dimension num_nodes by h_feats[-1]
		h = self.final(h)
		g.ndata['h'] = h
		# Go from node level features to graph level features by pooling
		h = self.pooling_layer(g, h)
		# h will now be vector of dimension num_classes
		return h

def reset_weights(self):
	'''
	Try resetting model weights to avoid
	weight leakage.
	'''
	for layer in self.children():
		if hasattr(layer, 'reset_parameters'):
			layer.reset_parameters()


class ClassifierSplit:
	def __init__(self, hparams, trainingDataset):
		#device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
		device = torch.device("cpu")
		self.trainingDataset = trainingDataset
		self.hparams = hparams
		if hparams.conv_layer_type == 'Classic':
			self.model = GCN_Classic(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses).to(device)
		elif hparams.conv_layer_type == 'GINConv':
			self.model = GCN_GINConv(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses, hparams.pooling).to(device)
		elif hparams.conv_layer_type == 'GraphConv':
			self.model = GCN_GraphConv(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses, hparams.pooling).to(device)
		elif hparams.conv_layer_type == 'SAGEConv':
			self.model = GCN_SAGEConv(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses, hparams.pooling).to(device)
		elif hparams.conv_layer_type == 'TAGConv':
			self.model = GCN_TAGConv(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses, hparams.pooling).to(device)
		elif hparams.conv_layer_type == 'GCN':
			self.model = GCN(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses).to(device)
		else:
			raise NotImplementedError

		if hparams.optimizer_str == "Adadelta":
			self.optimizer = torch.optim.Adadelta(self.model.parameters(), eps=hparams.eps, 
                                            lr=hparams.lr, rho=hparams.rho, weight_decay=hparams.weight_decay)
		elif hparams.optimizer_str == "Adagrad":
			self.optimizer = torch.optim.Adagrad(self.model.parameters(), eps=hparams.eps, 
                                            lr=hparams.lr, lr_decay=hparams.lr_decay, weight_decay=hparams.weight_decay)
		elif hparams.optimizer_str == "Adam":
			self.optimizer = torch.optim.Adam(self.model.parameters(), amsgrad=hparams.amsgrad, betas=hparams.betas, eps=hparams.eps, 
                                            lr=hparams.lr, maximize=hparams.maximize, weight_decay=hparams.weight_decay)
		self.use_gpu = hparams.use_gpu
		self.training_loss_list = []
		self.testing_loss_list = []
		self.training_accuracy_list = []
		self.testing_accuracy_list = []
		self.node_attr_key = trainingDataset.node_attr_key
		# train test split
		idx = torch.randperm(len(trainingDataset))
		num_train = int(len(trainingDataset) * hparams.split)
        
		train_sampler = SubsetRandomSampler(idx[:num_train])
		test_sampler = SubsetRandomSampler(idx[num_train:])
        
		self.train_dataloader = GraphDataLoader(trainingDataset, sampler=train_sampler, 
												batch_size=hparams.batch_size,
												drop_last=False)
		self.test_dataloader = GraphDataLoader(trainingDataset, sampler=test_sampler,
												batch_size=hparams.batch_size,
												drop_last=False)
	def train(self):
		#device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
		device = torch.device("cpu")
		# Init the loss and accuracy reporting lists
		self.training_accuracy_list = []
		self.training_loss_list = []
		self.testing_accuracy_list = []
		self.testing_loss_list = []

		# Run the training loop for defined number of epochs
		for _ in range(self.hparams.epochs):
			num_correct = 0
			num_tests = 0
			temp_loss_list = []

			# Iterate over the DataLoader for training data
			for batched_graph, labels in self.train_dataloader:
					
				# Zero the gradients
				self.optimizer.zero_grad()

				# Perform forward pass
				pred = self.model(batched_graph, batched_graph.ndata[self.node_attr_key].float()).to(device)
				# Compute loss
				if self.hparams.loss_function == "Negative Log Likelihood":
					logp = F.log_softmax(pred, 1)
					loss = F.nll_loss(logp, labels)
				elif self.hparams.loss_function == "Cross Entropy":
					loss = F.cross_entropy(pred, labels)

				# Save loss information for reporting
				temp_loss_list.append(loss.item())
				num_correct += (pred.argmax(1) == labels).sum().item()
				num_tests += len(labels)

				# Perform backward pass
				loss.backward()

				# Perform optimization
				self.optimizer.step()

			self.training_accuracy = num_correct / num_tests
			self.training_accuracy_list.append(self.training_accuracy)
			self.training_loss_list.append(sum(temp_loss_list) / len(temp_loss_list))
			self.test()
			self.testing_accuracy_list.append(self.testing_accuracy)
			self.testing_loss_list.append(self.testing_loss)
		if self.hparams.checkpoint_path is not None:
			# Save the entire model
			torch.save(self.model, self.hparams.checkpoint_path)

	def test(self):
		#device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
		device = torch.device("cpu")
		num_correct = 0
		num_tests = 0
		temp_testing_loss = []
		for batched_graph, labels in self.test_dataloader:
			pred = self.model(batched_graph, batched_graph.ndata[self.node_attr_key].float()).to(device)
			if self.hparams.loss_function == "Negative Log Likelihood":
				logp = F.log_softmax(pred, 1)
				loss = F.nll_loss(logp, labels)
			elif self.hparams.loss_function == "Cross Entropy":
				loss = F.cross_entropy(pred, labels)
			temp_testing_loss.append(loss.item())
			num_correct += (pred.argmax(1) == labels).sum().item()
			num_tests += len(labels)
		self.testing_loss = (sum(temp_testing_loss) / len(temp_testing_loss))
		self.testing_accuracy = num_correct / num_tests
		return self.testing_accuracy

class ClassifierKFold:
	def __init__(self, hparams, trainingDataset, validationDataset):
		self.trainingDataset = trainingDataset
		self.validationDataset = validationDataset
		self.hparams = hparams
		# at beginning of the script
		#device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
		device = torch.device("cpu")
		if hparams.conv_layer_type == 'Classic':
			self.model = GCN_Classic(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses).to(device)
		elif hparams.conv_layer_type == 'GINConv':
			self.model = GCN_GINConv(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses, hparams.pooling).to(device)
		elif hparams.conv_layer_type == 'GraphConv':
			self.model = GCN_GraphConv(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses, hparams.pooling).to(device)
		elif hparams.conv_layer_type == 'SAGEConv':
			self.model = GCN_SAGEConv(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses, hparams.pooling).to(device)
		elif hparams.conv_layer_type == 'TAGConv':
			self.model = GCN_TAGConv(trainingDataset.dim_nfeats, hparams.hidden_layers, 
                            trainingDataset.gclasses, hparams.pooling).to(device)
		else:
			raise NotImplementedError

		if hparams.optimizer_str == "Adadelta":
			self.optimizer = torch.optim.Adadelta(self.model.parameters(), eps=hparams.eps, 
                                            lr=hparams.lr, rho=hparams.rho, weight_decay=hparams.weight_decay)
		elif hparams.optimizer_str == "Adagrad":
			self.optimizer = torch.optim.Adagrad(self.model.parameters(), eps=hparams.eps, 
                                            lr=hparams.lr, lr_decay=hparams.lr_decay, weight_decay=hparams.weight_decay)
		elif hparams.optimizer_str == "Adam":
			self.optimizer = torch.optim.Adam(self.model.parameters(), amsgrad=hparams.amsgrad, betas=hparams.betas, eps=hparams.eps, 
                                            lr=hparams.lr, maximize=hparams.maximize, weight_decay=hparams.weight_decay)
		self.use_gpu = hparams.use_gpu
		self.training_loss_list = []
		self.testing_loss_list = []
		self.training_accuracy_list = []
		self.testing_accuracy_list = []
		self.node_attr_key = trainingDataset.node_attr_key

	def train(self):
		# The number of folds (This should come from the hparams)
		k_folds = self.hparams.k_folds

		# Init the loss and accuracy reporting lists
		self.training_accuracy_list = []
		self.training_loss_list = []
		self.testing_accuracy_list = []
		self.testing_loss_list = []

		# Set fixed random number seed
		torch.manual_seed(42)
		
		# Define the K-fold Cross Validator
		kfold = KFold(n_splits=k_folds, shuffle=True)

		# K-fold Cross-validation model evaluation
		for fold, (train_ids, test_ids) in enumerate(kfold.split(self.trainingDataset)):
			epoch_training_loss_list = []
			epoch_training_accuracy_list = []
			epoch_testing_loss_list = []
			epoch_testing_accuracy_list = []
			# Sample elements randomly from a given list of ids, no replacement.
			train_subsampler = torch.utils.data.SubsetRandomSampler(train_ids)
			test_subsampler = torch.utils.data.SubsetRandomSampler(test_ids)

			# Define data loaders for training and testing data in this fold
			self.train_dataloader = GraphDataLoader(self.trainingDataset, sampler=train_subsampler, 
												batch_size=self.hparams.batch_size,
												drop_last=False)
			self.test_dataloader = GraphDataLoader(self.trainingDataset, sampler=test_subsampler,
												batch_size=self.hparams.batch_size,
												drop_last=False)
			# Init the neural network
			self.model.apply(reset_weights)

			# Run the training loop for defined number of epochs
			for _ in range(self.hparams.epochs):
				num_correct = 0
				num_tests = 0
				training_temp_loss_list = []

				# Iterate over the DataLoader for training data
				for batched_graph, labels in self.train_dataloader:
					
					# Zero the gradients
					self.optimizer.zero_grad()

					# Perform forward pass
					pred = self.model(batched_graph, batched_graph.ndata[self.node_attr_key].float())

					# Compute loss
					if self.hparams.loss_function == "Negative Log Likelihood":
						logp = F.log_softmax(pred, 1)
						loss = F.nll_loss(logp, labels)
					elif self.hparams.loss_function == "Cross Entropy":
						loss = F.cross_entropy(pred, labels)

					# Save loss information for reporting
					training_temp_loss_list.append(loss.item())
					num_correct += (pred.argmax(1) == labels).sum().item()
					num_tests += len(labels)

					# Perform backward pass
					loss.backward()

					# Perform optimization
					self.optimizer.step()

				self.training_accuracy = num_correct / num_tests
				epoch_training_accuracy_list.append(self.training_accuracy)
				epoch_training_loss_list.append(sum(training_temp_loss_list) / len(training_temp_loss_list))
				self.test()
				epoch_testing_accuracy_list.append(self.testing_accuracy)
				epoch_testing_loss_list.append(self.testing_loss)
			if self.hparams.checkpoint_path is not None:
				# Save the entire model
				torch.save(self.model, self.hparams.checkpoint_path+"-fold_"+str(fold))
			self.training_accuracy_list.append(epoch_training_accuracy_list)
			self.training_loss_list.append(epoch_training_loss_list)
			self.testing_accuracy_list.append(epoch_testing_accuracy_list)
			self.testing_loss_list.append(epoch_testing_loss_list)

	def test(self):
		num_correct = 0
		num_tests = 0
		temp_testing_loss = []
		for batched_graph, labels in self.test_dataloader:
			pred = self.model(batched_graph, batched_graph.ndata[self.node_attr_key].float())
			if self.hparams.loss_function == "Negative Log Likelihood":
				logp = F.log_softmax(pred, 1)
				loss = F.nll_loss(logp, labels)
			elif self.hparams.loss_function == "Cross Entropy":
				loss = F.cross_entropy(pred, labels)
			temp_testing_loss.append(loss.item())
			num_correct += (pred.argmax(1) == labels).sum().item()
			num_tests += len(labels)
		self.testing_loss = (sum(temp_testing_loss) / len(temp_testing_loss))
		self.testing_accuracy = num_correct / num_tests
		return self.testing_accuracy

	def accuracy(self, item):
		dgl_labels, dgl_predictions = item
	
		num_correct = 0
		for i in range(len(dgl_predictions)):
			if dgl_predictions[i] == dgl_labels[i]:
				num_correct = num_correct + 1
		size = len(dgl_predictions)
		return (num_correct / len(dgl_predictions))

	def predict(self):
		#device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
		device = torch.device("cpu")
		predicted_labels = []
		idx = torch.randperm(len(self.validationDataset))
		num_train = int(len(self.validationDataset))
		sampler = SubsetRandomSampler(idx[:num_train])
		dataloader = GraphDataLoader(self.validationDataset, sampler=sampler, 
                                                batch_size=1,
                                                drop_last=False)
		num_correct = 0
		num_tests = 0
		for batched_graph, labels in dataloader:
			pred = self.model(batched_graph, batched_graph.ndata[self.node_attr_key].float()).to(device)
			num_correct += (pred.argmax(1) == labels).sum().item()
			num_tests += len(labels)
		accuracy = num_correct / num_tests
		return accuracy

	def validate(self):
		#device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
		device = torch.device("cpu")
		# Set training to 100% of the data, validate, and save a final model
		idx = torch.randperm(len(self.trainingDataset))
		num_train = int(len(self.trainingDataset))
		sampler = SubsetRandomSampler(idx[:num_train])
		dataloader = GraphDataLoader(self.trainingDataset, sampler=sampler, 
                                                batch_size=self.hparams.batch_size,
                                                drop_last=False)
		# Once a model is chosen, train on all the data and save
		for e in range(self.hparams.epochs):
			num_correct = 0
			num_tests = 0
			for batched_graph, labels in dataloader:
				#pred = self.model(batched_graph, batched_graph.ndata['attr'].float()).to(device)
				pred = self.model(batched_graph, batched_graph.ndata[self.node_attr_key].float()).to(device)
				if self.hparams.loss_function == "Negative Log Likelihood":
					logp = F.log_softmax(pred, 1)
					loss = F.nll_loss(logp, labels)
				elif self.hparams.loss_function == "Cross Entropy":
					loss = F.cross_entropy(pred, labels)
				num_correct += (pred.argmax(1) == labels).sum().item()
				num_tests += len(labels)
				self.optimizer.zero_grad()
				loss.backward()
				self.optimizer.step()
			training_accuracy = num_correct / num_tests
			validation_accuracy = self.predict()
			if validation_accuracy >= training_accuracy and validation_accuracy > 0.6:
				break
		print("Validation - Stopped at Epoch:", e+1)
		if self.hparams.checkpoint_path is not None:
			# Save the entire model
			torch.save(self.model, self.hparams.checkpoint_path)

def runItem(i, item):
	start = time.time()
	hparams, trainingDataset, validationDataset = item
	if hparams.cv_type == "Holdout":
		classifier = ClassifierSplit(hparams, trainingDataset)
		classifier.train()
		accuracy = classifier.test()
	elif hparams.cv_type == "K-Fold":
		classifier = ClassifierKFold(hparams, trainingDataset, validationDataset)
		classifier.train()
		final_epochs = classifier.validate()

		# Transpose the fold data
		temp_list = Replication.transposeList(classifier.training_accuracy_list)
		tr_a_l = []
		for l in temp_list:
			tr_a_l.append((sum(l) / len(l)))
		temp_list = Replication.transposeList(classifier.training_loss_list)
		tr_l_l = []
		for l in temp_list:
			tr_l_l.append((sum(l) / len(l)))
		temp_list = Replication.transposeList(classifier.testing_accuracy_list)
		te_a_l = []
		for l in temp_list:
			te_a_l.append((sum(l) / len(l)))
		temp_list = Replication.transposeList(classifier.testing_loss_list)
		te_l_l = []
		for l in temp_list:
			te_l_l.append((sum(l) / len(l)))

		classifier.training_accuracy_list = tr_a_l
		classifier.training_loss_list = tr_l_l
		classifier.testing_accuracy_list = te_a_l
		classifier.testing_loss_list = te_l_l
	
	end = time.time()
	duration = round(end - start,3)
	utcnow = datetime.utcnow()
	timestamp_str = "UTC-"+str(utcnow.year)+"-"+str(utcnow.month)+"-"+str(utcnow.day)+"-"+str(utcnow.hour)+"-"+str(utcnow.minute)+"-"+str(utcnow.second)
	epoch_list = list(range(1,classifier.hparams.epochs+1))
	data_list = [timestamp_str, duration, classifier.model, classifier.hparams.optimizer_str, classifier.hparams.cv_type, classifier.hparams.split, classifier.hparams.k_folds, classifier.hparams.hidden_layers, classifier.hparams.conv_layer_type, classifier.hparams.pooling, classifier.hparams.lr, classifier.hparams.batch_size, list(range(1,classifier.hparams.epochs+1)), classifier.training_accuracy_list, classifier.testing_accuracy_list, classifier.training_loss_list, classifier.testing_loss_list]
	d2 = [[timestamp_str], [duration], [classifier.hparams.optimizer_str], [classifier.hparams.cv_type], [classifier.hparams.split], [classifier.hparams.k_folds], classifier.hparams.hidden_layers, [classifier.hparams.conv_layer_type], [classifier.hparams.pooling], [classifier.hparams.lr], [classifier.hparams.batch_size], epoch_list, classifier.training_accuracy_list, classifier.testing_accuracy_list, classifier.training_loss_list, classifier.testing_loss_list]
	d2 = Replication.iterate(d2)
	d2 = Replication.transposeList(d2)
	
	data = {'TimeStamp': "UTC-"+str(utcnow.year)+"-"+str(utcnow.month)+"-"+str(utcnow.day)+"-"+str(utcnow.hour)+"-"+str(utcnow.minute)+"-"+str(utcnow.second),
			'Duration': [duration],
	        'Optimizer': [classifier.hparams.optimizer_str],
			'CV Type': [classifier.hparams.cv_type],
			'Split': [classifier.hparams.split],
			'K-Folds': [classifier.hparams.k_folds],
			'HL Widths': [classifier.hparams.hidden_layers],
			'Conv Layer Type': [classifier.hparams.conv_layer_type],
			'Pooling': [classifier.hparams.pooling],
			'Learning Rate': [classifier.hparams.lr],
			'Batch Size': [classifier.hparams.batch_size],
			'Epochs': [classifier.hparams.epochs],
			'Training Accuracy': [classifier.training_accuracy_list],
			'Testing Accuracy': [classifier.testing_accuracy_list],
			'Training Loss': [classifier.training_loss_list],
			'Testing Loss': [classifier.testing_loss_list]
        }
	if classifier.hparams.results_path:
		df = pd.DataFrame(d2, columns= ['TimeStamp', 'Duration', 'Optimizer', 'CV Type', 'Split', 'K-Folds', 'HL Widths', 'Conv Layer Type', 'Pooling', 'Learning Rate', 'Batch Size', 'Epochs', 'Training Accuracy', 'Testing Accuracy', 'Training Loss', 'Testing Loss'])
		if i == 0:
			df.to_csv(classifier.hparams.results_path, mode='w+', index = False, header=True)
		else:
			df.to_csv(classifier.hparams.results_path, mode='a', index = False, header=False)


	return data_list

def sv_execute(node):
	autorunList = node.inputs['Auto-Run'].sv_get(deepcopy=True)
	autorunList = Replication.flatten(autorunList)
	if not autorunList[0]:
		return
	start = time.time()
	hyperparametersList = node.inputs['Hyperparameters'].sv_get(deepcopy=False)
	trainingDatasetList = node.inputs['Training Dataset'].sv_get(deepcopy=False)
	validationDatasetList = node.inputs['Validation Dataset'].sv_get(deepcopy=False)
	hyperparametersList = Replication.flatten(hyperparametersList)
	trainingDatasetList = Replication.flatten(trainingDatasetList)
	validationDatasetList = Replication.flatten(validationDatasetList)
	inputs = [hyperparametersList, trainingDatasetList, validationDatasetList]
	if ((node.Replication) == "Trim"):
		inputs = Replication.trim(inputs)
		inputs = Replication.transposeList(inputs)
	elif ((node.Replication) == "Default") or ((node.Replication) == "Iterate"):
		inputs = Replication.iterate(inputs)
		inputs = Replication.transposeList(inputs)
	elif ((node.Replication) == "Repeat"):
		inputs = Replication.repeat(inputs)
		inputs = Replication.transposeList(inputs)
	elif ((node.Replication) == "Interlace"):
		inputs = list(Replication.interlace(inputs))
	outputs = []
	timestampList = []
	classifierList = []
	optimizerList = []
	cv_typeList = []
	splitList = []
	k_foldsList = []
	hidden_layersList = []
	conv_layer_typeList = []
	poolingList = []
	learning_rateList = []
	batch_sizeList = []
	durationList = []
	epochsList = []
	training_accuracyList = []
	testing_accuracyList = []
	training_lossList = []
	testing_lossList = []
	for i, anInput in enumerate(inputs):
		output = runItem(i, anInput)
		timestamp, duration, classifier, optimizer_str, cv_type, split, k_folds, hidden_layers, conv_layer_type, pooling, learning_rate, batch_size, epochs, training_accuracy, testing_accuracy, training_loss, testing_loss = output
		timestampList.append(timestamp)
		durationList.append(duration)
		classifierList.append(classifier)
		optimizerList.append(optimizer_str)
		cv_typeList.append(cv_type)
		splitList.append(split)
		k_foldsList.append(k_folds)
		hidden_layersList.append(hidden_layers)
		conv_layer_typeList.append(conv_layer_type)
		poolingList.append(pooling)
		learning_rateList.append(learning_rate)
		batch_sizeList.append(batch_size)
		epochsList.append(epochs)
		training_accuracyList.append(training_accuracy)
		testing_accuracyList.append(testing_accuracy)
		training_lossList.append(training_loss)
		testing_lossList.append(testing_loss)

	node.outputs['Timestamp'].sv_set(timestampList)
	node.outputs['Duration'].sv_set(durationList)
	node.outputs['Classifier'].sv_set(classifierList)
	node.outputs['Optimizer'].sv_set(optimizerList)
	node.outputs['CV Type'].sv_set(k_foldsList)
	node.outputs['Split'].sv_set(k_foldsList)
	node.outputs['K-Folds'].sv_set(k_foldsList)
	node.outputs['Hidden Layers'].sv_set(hidden_layersList)
	node.outputs['Conv Layer Type'].sv_set(conv_layer_typeList)
	node.outputs['Pooling'].sv_set(poolingList)
	node.outputs['Learning Rate'].sv_set(learning_rateList)
	node.outputs['Batch Size'].sv_set(batch_sizeList)
	node.outputs['Epochs'].sv_set(epochsList)
	node.outputs['Training Accuracy'].sv_set(training_accuracyList)
	node.outputs['Testing Accuracy'].sv_set(testing_accuracyList)
	node.outputs['Training Loss'].sv_set(training_lossList)
	node.outputs['Testing Loss'].sv_set(testing_lossList)
	
	'''
	tree = node.id_data
	UpdateTree.get(tree)
	tree.sv_process = True
	from_nodes = tree.inputs
	to_nodes = tree.outputs 
	loop_nodes = from_nodes.intersection(to_nodes)
	sort_loop_nodes = tree.sort_nodes(loop_nodes)
	for node in sort_loop_nodes[1:-1]:
		try:
			tree.update_node(node, suppress=False)
		except Exception:
			raise Exception(f"Iteration number: {i+1}") 

	#update_list = make_tree_from_nodes([node.name], tree)
	#update_list = update_list[1:]
	#do_update(update_list, tree.nodes)
	'''
	end = time.time()
	print("DGL.TrainClassifier Operation consumed "+str(round(end - start,2)*1000)+" ms")

class SvDGLTrainClassifierRun(bpy.types.Operator, SvGenericNodeLocator):

	bl_idname = "dgl.trainclassifierrun"
	bl_label = "DGL.TrainClassifierRun"
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_execute(self, context, node):
		sv_execute(node)


class SvDGLTrainClassifier(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Train the DGL Classifier with the input Dataset and the input Hyperparameters   
	"""
	bl_idname = 'SvDGLTrainClassifier'
	bl_label = 'DGL.TrainClassifier'
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	HyperparametersProp: StringProperty(name="Hyperparameters", update=updateNode)
	TrainingDatasetProp: StringProperty(name="Training Dataset", update=updateNode)
	ValidationDatasetProp: StringProperty(name="Validation Dataset", update=updateNode)
	AutoRunProp: BoolProperty(name="Auto Run", description="Automatically train and test the classifier", default=False, update=updateNode)

	def sv_init(self, context):
		self.width = 200
		self.inputs.new('SvStringsSocket', 'Hyperparameters').prop_name="HyperparametersProp"
		self.inputs.new('SvStringsSocket', 'Training Dataset').prop_name="TrainingDatasetProp"
		self.inputs.new('SvStringsSocket', 'Validation Dataset').prop_name="ValidationDatasetProp"
		self.inputs.new('SvStringsSocket', 'Auto-Run').prop_name="AutoRunProp"
		self.outputs.new('SvStringsSocket', 'Timestamp')
		self.outputs.new('SvStringsSocket', 'Duration')
		self.outputs.new('SvStringsSocket', 'Classifier')
		self.outputs.new('SvStringsSocket', 'Optimizer')
		self.outputs.new('SvStringsSocket', 'CV Type')
		self.outputs.new('SvStringsSocket', 'Split')
		self.outputs.new('SvStringsSocket', 'K-Folds')
		self.outputs.new('SvStringsSocket', 'Hidden Layers')
		self.outputs.new('SvStringsSocket', 'Conv Layer Type')
		self.outputs.new('SvStringsSocket', 'Pooling')
		self.outputs.new('SvStringsSocket', 'Learning Rate')
		self.outputs.new('SvStringsSocket', 'Batch Size')
		self.outputs.new('SvStringsSocket', 'Epochs')
		self.outputs.new('SvStringsSocket', 'Training Accuracy')
		self.outputs.new('SvStringsSocket', 'Testing Accuracy')
		self.outputs.new('SvStringsSocket', 'Training Loss')
		self.outputs.new('SvStringsSocket', 'Testing Loss')
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "SvDGLTrainClassifier_draw_socket"

	def SvDGLTrainClassifier_draw_socket(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.6)
		#split.row().label(text=socket.name+ '. ' + SvGetSocketInfo(socket))
		split.row().label(text=socket.name + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		#row = layout.row(align=True)
		#row.scale_y = 2
		#self.wrapper_tracked_ui_draw_op(row, "dgl.trainclassifierrun", icon='PLAY', text="RUN")

	def process(self):
		for socket in self.outputs:
			socket.sv_set([[0]])
		autorunList = self.inputs['Auto-Run'].sv_get(deepcopy=True)
		autorunList = Replication.flatten(autorunList)
		if autorunList[0]:
			sv_execute(self)
		


def register():
	bpy.utils.register_class(SvDGLTrainClassifier)
	bpy.utils.register_class(SvDGLTrainClassifierRun)

def unregister():
	bpy.utils.unregister_class(SvDGLTrainClassifier)
	bpy.utils.unregister_class(SvDGLTrainClassifierRun)
