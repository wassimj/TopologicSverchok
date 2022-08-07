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
	test_dataset, classifier, node_attr_key  = item
	labels = []
	probabilities = []
	for item in test_dataset:
		graph = item[0]
		print("Node Label:", graph.ndata[node_attr_key].float())
		pred = classifier(graph, graph.ndata[node_attr_key].float())
		labels.append(pred.argmax(1).item())
		probability = (torch.nn.functional.softmax(pred, dim=1).tolist())
		probability = probability[0]
		temp_probability = []
		for p in probability:
			temp_probability.append(round(p, 3))
		probabilities.append(temp_probability)
	return [labels, probabilities]

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDGLPredict(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Predicts the labels of the input dataset using the input classifier
	"""
	
	bl_idname = 'SvDGLPredict'
	bl_label = 'DGL.Predict'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	NodeAttrKeyLabel: StringProperty(name='Node Attr Key', default='node_attr', update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Dataset')
		self.inputs.new('SvStringsSocket', 'Classifier')
		self.inputs.new('SvStringsSocket', 'Node Attr Key').prop_name='NodeAttrKeyLabel'
		self.outputs.new('SvStringsSocket', 'Predictions')
		self.outputs.new('SvStringsSocket', 'Probabilities')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		datasetList = self.inputs['Dataset'].sv_get(deepcopy=True)
		classifierList = self.inputs['Classifier'].sv_get(deepcopy=True)
		datasetList = Replication.flatten(datasetList)
		classifierList = Replication.flatten(classifierList)
		node_attr_keyList = self.inputs['Node Attr Key'].sv_get(deepcopy=True)
		node_attr_keyList = Replication.flatten(node_attr_keyList)
		inputs = [datasetList, classifierList, node_attr_keyList]
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
		probabilities = []
		outputs = []
		for anInput in inputs:
			prediction, probability = processItem(anInput)
			predictions.append(prediction)
			probabilities.append(probability)
		self.outputs['Predictions'].sv_set(predictions)
		self.outputs['Probabilities'].sv_set(probabilities)

def register():
	bpy.utils.register_class(SvDGLPredict)

def unregister():
	bpy.utils.unregister_class(SvDGLPredict)
