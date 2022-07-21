#import sys
#sys.path.append(r"D:\Anaconda3\envs\py310\Lib\site-packages")
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
#from sverchok.core.socket_data import SvGetSocketInfo

import torch
from . import Replication
import os

checkpoint_path = os.path.join(os.path.expanduser('~'), "dgl_classifier.pt")
results_path = os.path.join(os.path.expanduser('~'), "dgl_results.csv")
cv_types = [("Holdout", "Holdout", "", 1),
				  ("K-Fold", "K-Fold", "", 2)]
loss_functions = [("Negative Log Likelihood", "Negative Log Likelihood", "", 1),
				  ("Cross Entropy", "Cross Entropy", "", 2)]
conv_layer_types = [("GINConv", "GINConv", "", 1),
				  ("GraphConv", "GraphConv", "", 2),
				  ("SAGEConv", "SAGEConv", "", 3),
				  ("TAGConv", "TAGConv", "", 4),
				  ("Classic", "Classic", "", 5)]
pooling = [("AvgPooling", "AvgPooling", "", 1),
				  ("MaxPooling", "MaxPooling", "", 2),
				  ("SumPooling", "SumPooling", "", 3)]
class Hparams:
	def __init__(self, optimizer_str="Adam", amsgrad=False, betas=(0.9, 0.999), eps=1e-6, lr=0.001, lr_decay= 0, maximize=False, rho=0.9, weight_decay=0, cv_type="Holdout", split=0.2, k_folds=5, hidden_layers=[32], conv_layer_type='SAGEConv', pooling="AvgPooling", batch_size=32, epochs=1, 
                 use_gpu=False, loss_function="Cross-Entropy", checkpoint_path=checkpoint_path, results_path=results_path):
		"""
		Parameters
		----------
		cv : str
			An int value in the range of 0 to X to define the method of cross-validation
			"Holdout": Holdout
			"K-Fold": K-Fold cross validation
		k_folds : int
			An int value in the range of 2 to X to define the number of k-folds for cross-validation. Default is 5.
		split : float
			A float value in the range of 0 to 1 to define the split of train
			and test data. A default value of 0.2 means 20% of data will be
			used for testing and remaining 80% for training
		hidden_layers : list
			List of hidden neurons for each layer such as [32] will mean
			that there is one hidden layers in the network with 32 neurons
		optimizer : torch.optim object
			This will be the selected optimizer from torch.optim package. By
			default, torch.optim.Adam is selected
		learning_rate : float
			a step value to be used to apply the gradients by optimizer
		batch_size : int
			to define a set of samples to be used for training and testing in 
			each step of an epoch
		epochs : int
			An epoch means training the neural network with all the training data for one cycle. In an epoch, we use all of the data exactly once. A forward pass and a backward pass together are counted as one pass
		checkpoint_path: str
			Path to save the classifier after training. It is preferred for 
			the path to have .pt extension
		use_GPU : use the GPU. Otherwise, use the CPU

		Returns
		-------
		None

		"""
        
		self.optimizer_str = optimizer_str
		self.amsgrad = amsgrad
		self.betas = betas
		self.eps = eps
		self.lr = lr
		self.lr_decay = lr_decay
		self.maximize = maximize
		self.rho = rho
		self.weight_decay = weight_decay
		self.cv_type = cv_type
		self.split = split
		self.k_folds = k_folds
		self.hidden_layers = hidden_layers
		self.conv_layer_type = conv_layer_type
		self.pooling = pooling
		self.batch_size = batch_size
		self.epochs = epochs
		self.use_gpu = use_gpu
		self.loss_function = loss_function
		self.checkpoint_path = checkpoint_path
		self.results_path = results_path

def processItem(item):
	optimizer, cv_type, split, k_folds, hidden_layers_str, conv_layer_type, pooling, batch_size, epochs, use_gpu, loss_function, checkpoint_path, results_path = item
	amsgrad = False
	betas=(0.9, 0.999)
	eps=1e-6
	lr=0.001
	lr_decay= 0
	maximize=False
	rho=0.9
	weight_decay=0
	if optimizer[0] == "Adadelta":
		optimizer_str, eps, lr, rho, weight_decay = optimizer
	elif optimizer[0] == "Adagrad":
		optimizer_str, eps, lr, lr_decay, weight_decay = optimizer
	elif optimizer[0] == "Adam":
		optimizer_str, amsgrad, betas, eps, lr, maximize, weight_decay = optimizer
	hl_str_list = hidden_layers_str.split()
	hidden_layers = []
	for hl in hl_str_list:
		if hl != None and hl.isnumeric():
			hidden_layers.append(int(hl))
	# Classifier: Make sure the file extension is .pt
	ext = checkpoint_path[len(checkpoint_path)-3:len(checkpoint_path)]
	if ext.lower() != ".pt":
		checkpoint_path = checkpoint_path+".pt"
	# Results: Make sure the file extension is .csv
	ext = results_path[len(results_path)-4:len(results_path)]
	if ext.lower() != ".csv":
		results_path = results_path+".csv"
	return Hparams(optimizer_str, amsgrad, betas, eps, lr, lr_decay, maximize, rho, weight_decay, cv_type, split, k_folds, hidden_layers, conv_layer_type, pooling, batch_size, epochs, use_gpu, loss_function, checkpoint_path, results_path)

def update_sockets(self, context):
	# hide all input sockets
	self.inputs['Optimizer'].hide_safe = False
	self.inputs['Split'].hide_safe = True
	self.inputs['K-Folds'].hide_safe = True
	self.inputs['HL Widths'].hide_safe = False
	self.inputs['Conv Layer Type'].hide_safe = False
	self.inputs['Pooling'].hide_safe = False
	self.inputs['Batch Size'].hide_safe = False
	self.inputs['Epochs'].hide_safe = False
	self.inputs['Use GPU'].hide_safe = False
	self.inputs['Loss Function'].hide_safe = False
	self.inputs['Classifier File Path'].hide_safe = False
	self.inputs['Results File Path'].hide_safe = False
	print("CV Type:", self.CVType)
	if self.CVType == "Holdout":
		self.inputs['Split'].hide_safe = False
	elif self.CVType == "K-Fold":
		self.inputs['K-Folds'].hide_safe = False
	updateNode(self, context)
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDGLHyperparameters(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a DGL Hyperparameters Object from the input parameters
	"""
	
	bl_idname = 'SvDGLHyperparameters'
	bl_label = 'DGL.Hyperparameters'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	OptimizersProp: StringProperty(name="Optimizer", description="This will be the selected optimizer from the torch.optim package.", update=updateNode)
	CVType: EnumProperty(name="Cross Validation Type", description="The method of cross validation (Default: Holdout)", default="Holdout", items=cv_types, update=update_sockets)
	SplitProp: FloatProperty(name="Split", description="A float value in the range of 0 to 1 to define the split of train and test data. A value of 0.2 means 20% of data will be used for testing and remaining 80% for training. The default is 0.2", default=0.2, min=0, max=1, update=updateNode)
	K_FoldsProp: IntProperty(name="K-Folds", description="An integer value to define the number of k-folds for cross-validation (Default 5)", default=5, min=2, update=updateNode)
	HiddenLayersProp: StringProperty(name="HL Widths", description="A space-separated string representing the number of neurons in each hidden layer. For example, \"32 16\" means that there are two hidden layers in the network with 32 neurons and 16 neurons respectively. The default is one hidden layer with 32 neuorns", default="32", update=updateNode)
	ConvLayerTypeProp: EnumProperty(name="Conv Layer Type", description="The type of convolution layers (Default: SAGEConv)", default="SAGEConv", items=conv_layer_types, update=updateNode)
	PoolingProp: EnumProperty(name="Pooling", description="Pooling type (Default: AvgPooling)", default="AvgPooling", items=pooling, update=updateNode)
	BatchSizeProp: IntProperty(name="Batch Size", description="Defines a set of samples to be used for training and testing in each step of an epoch. The default is 1 batch", default=1, min=1, update=updateNode)
	EpochsProp: IntProperty(name="Epochs", description="An epoch means training the neural network with all the training data for one cycle. In an epoch, we use all of the data exactly once. A forward pass and a backward pass together are counted as one pass. The default is 1 epoch", default=1, min=1, update=updateNode)
	UseGPUProp: BoolProperty(name="Use GPU", description="Ask PyTorch to use CUDA GPU.", default=False, update=updateNode)
	LossFunctionProp: EnumProperty(name="Loss Function", description="The function that will determine your model\'s performance by comparing its predicted output with the expected output (Default: Cross Entropy)", default="Cross Entropy", items=loss_functions, update=updateNode)
	ClassifierFilePathProp: StringProperty(name="Classifier File Path", description="Path to save the classifier after training. It is preferred for the path to have .pt extension. Default is "+checkpoint_path,default=checkpoint_path, update=updateNode)
	ResultsFilePathProp: StringProperty(name="Results File Path", description="Path to save the results after training. It is preferred for the path to have .csv extension. Default is "+results_path,default=results_path, update=updateNode)

	def sv_init(self, context):
		self.width = 300
		self.inputs.new('SvStringsSocket', 'Split').prop_name='SplitProp'
		self.inputs.new('SvStringsSocket', 'K-Folds').prop_name='K_FoldsProp'
		self.inputs.new('SvStringsSocket', 'Optimizer').prop_name='OptimizersProp'
		self.inputs.new('SvStringsSocket', 'HL Widths').prop_name = 'HiddenLayersProp'
		self.inputs.new('SvStringsSocket', 'Conv Layer Type').prop_name = 'ConvLayerTypeProp'
		self.inputs.new('SvStringsSocket', 'Pooling').prop_name = 'PoolingProp'
		self.inputs.new('SvStringsSocket', 'Batch Size').prop_name='BatchSizeProp'
		self.inputs.new('SvStringsSocket', 'Epochs').prop_name='EpochsProp'
		self.inputs.new('SvStringsSocket', 'Use GPU').prop_name='UseGPUProp'
		self.inputs.new('SvStringsSocket', 'Loss Function').prop_name="LossFunctionProp"
		self.inputs.new('SvFilePathSocket', 'Classifier File Path').prop_name='ClassifierFilePathProp'
		self.inputs.new('SvFilePathSocket', 'Results File Path').prop_name='ResultsFilePathProp'
		self.outputs.new('SvStringsSocket', 'Hyperparameters')
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "SvDGLHyperparameters_draw_socket"
		update_sockets(self, context)

	def SvDGLHyperparameters_draw_socket(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.3)
		#split.row().label(text=socket.name+ '. ' + SvGetSocketInfo(socket))
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "CVType", expand=False, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not (self.inputs['Optimizer'].is_linked):
			raise Exception("DGL.Hyperparameters - Error: No optimizer has been linked. Please add a DGL.Optimizer Node.")
		optimizerList = self.inputs['Optimizer'].sv_get(deepcopy=True)
		cvTypeList = [self.CVType]
		splitList = self.inputs['Split'].sv_get(deepcopy=True)
		k_FoldsList = self.inputs['K-Folds'].sv_get(deepcopy=True)
		hiddenLayersList = self.inputs['HL Widths'].sv_get(deepcopy=True)
		convLayerTypesList = self.inputs['Conv Layer Type'].sv_get(deepcopy=True)
		poolingList = self.inputs['Pooling'].sv_get(deepcopy=True)
		batchSizeList = self.inputs['Batch Size'].sv_get(deepcopy=True)
		epochsList = self.inputs['Epochs'].sv_get(deepcopy=True)
		useGPUList = self.inputs['Use GPU'].sv_get(deepcopy=True)
		lossFunctionList = self.inputs['Loss Function'].sv_get(deepcopy=True)
		classifierFilePathList = self.inputs['Classifier File Path'].sv_get(deepcopy=True)
		resultsFilePathList = self.inputs['Results File Path'].sv_get(deepcopy=True)
		#optimizerList = Replication.flatten(optimizerList)
		#cvTypeList = Replication.flatten(cvTypeList)
		splitList = Replication.flatten(splitList)
		k_FoldsList = Replication.flatten(k_FoldsList)
		hiddenLayersList = Replication.flatten(hiddenLayersList)
		convLayerTypesList = Replication.flatten(convLayerTypesList)
		poolingList = Replication.flatten(poolingList)
		batchSizeList = Replication.flatten(batchSizeList)
		epochsList = Replication.flatten(epochsList)
		useGPUList = Replication.flatten(useGPUList)
		lossFunctionList = Replication.flatten(lossFunctionList)
		classifierFilePathList = Replication.flatten(classifierFilePathList)
		resultsFilePathList = Replication.flatten(resultsFilePathList)
		inputs = [optimizerList, cvTypeList, splitList, k_FoldsList, hiddenLayersList, convLayerTypesList, poolingList, batchSizeList, epochsList, useGPUList, lossFunctionList, classifierFilePathList, resultsFilePathList]
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
		self.outputs['Hyperparameters'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDGLHyperparameters)

def unregister():
	bpy.utils.unregister_class(SvDGLHyperparameters)
