import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import torch
from . import Replication

def processItem(item):
	"""
    
	Parameters
	----------
	model_checkpoint_path : str
		Path for the entire model 
	test_dataset : list
		A list containing several dgl graphs for prediction

	Returns
	-------
	Labels for the test graphs in test_dataset

	"""
	dataset, classifier  = item
	predictions = []
	labels = []
	if dataset.name == "cora_v2":
		g = dataset[0]
	else:
		g = dataset[0][0]
	print(">>>>>>> G: ", g)
	features = g.ndata['feat']
	labels.append(g.ndata['label'].tolist())
	# Forward
	logits = classifier(g, features)
	# Compute prediction
	pred = logits.argmax(1).tolist()
	predictions.append(pred)
	return [predictions, labels]

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDGLPredict_NC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Predicts the labels of the nodes of the input dataset using the input classifier
	"""
	
	bl_idname = 'SvDGLPredict_NC'
	bl_label = 'DGL.Predict_NC'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	NodeAttrKeyLabel: StringProperty(name='Node Attr Key', default='node_attr', update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Dataset')
		self.inputs.new('SvStringsSocket', 'Classifier')
		self.outputs.new('SvStringsSocket', 'Predictions')
		self.outputs.new('SvStringsSocket', 'Labels')


	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		datasetList = self.inputs['Dataset'].sv_get(deepcopy=True)
		classifierList = self.inputs['Classifier'].sv_get(deepcopy=True)
		datasetList = Replication.flatten(datasetList)
		classifierList = Replication.flatten(classifierList)
		inputs = [datasetList, classifierList]
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
		predictions = []
		labels = []
		outputs = []
		for anInput in inputs:
			prediction, label = processItem(anInput)
			predictions.append(prediction)
			labels.append(label)
		self.outputs['Predictions'].sv_set(predictions)
		self.outputs['Labels'].sv_set(labels)

def register():
	bpy.utils.register_class(SvDGLPredict_NC)

def unregister():
	bpy.utils.unregister_class(SvDGLPredict_NC)
