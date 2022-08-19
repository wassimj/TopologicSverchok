import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import torch
from . import Replication, DGLDatasetGraphs_NC

def processItem(item):
	classifier, dataset  = item
	allLabels = []
	allPredictions = []
	trainLabels = []
	trainPredictions = []
	valLabels = []
	valPredictions = []
	testLabels = []
	testPredictions = []
	
	graphs = DGLDatasetGraphs_NC.processItem(dataset)
	for g in graphs:
		if not g.ndata:
			continue
		train_mask = g.ndata['train_mask']
		val_mask = g.ndata['val_mask']
		test_mask = g.ndata['test_mask']
		features = g.ndata['feat']
		labels = g.ndata['label']
		train_labels = labels[train_mask]
		val_labels = labels[val_mask]
		test_labels = labels[test_mask]
		allLabels.append(labels.tolist())
		trainLabels.append(train_labels.tolist())
		valLabels.append(val_labels.tolist())
		testLabels.append(test_labels.tolist())
		
		# Forward
		logits = classifier(g, features)
		train_logits = logits[train_mask]
		val_logits = logits[val_mask]
		test_logits = logits[test_mask]
		
		# Compute prediction
		predictions = logits.argmax(1)
		train_predictions = train_logits.argmax(1)
		val_predictions = val_logits.argmax(1)
		test_predictions = test_logits.argmax(1)
		allPredictions.append(predictions.tolist())
		trainPredictions.append(train_predictions.tolist())
		valPredictions.append(val_predictions.tolist())
		testPredictions.append(test_predictions.tolist())
		
	return [Replication.flatten(allLabels), Replication.flatten(allPredictions),Replication.flatten(trainLabels), Replication.flatten(trainPredictions), Replication.flatten(valLabels), Replication.flatten(valPredictions), Replication.flatten(testLabels), Replication.flatten(testPredictions)]

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDGLPredict_NC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Predicts the labels of the nodes of the input dataset using the input classifier
	"""
	
	bl_idname = 'SvDGLPredict_NC'
	bl_label = 'DGL.Predict_NC'
	bl_icon = 'SELECT_DIFFERENCE'

	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Classifier')
		self.inputs.new('SvStringsSocket', 'Dataset')
		self.outputs.new('SvStringsSocket', 'All Labels')
		self.outputs.new('SvStringsSocket', 'All Predictions')
		self.outputs.new('SvStringsSocket', 'Train Labels')
		self.outputs.new('SvStringsSocket', 'Train Predictions')
		self.outputs.new('SvStringsSocket', 'Val Labels')
		self.outputs.new('SvStringsSocket', 'Val Predictions')
		self.outputs.new('SvStringsSocket', 'Test Labels')
		self.outputs.new('SvStringsSocket', 'Test Predictions')
		
		self.width = 175
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Replication")
		split.row().prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs_nested = []
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		inputs_replicated = Replication.replicateInputs(inputs_flat, self.Replication)
		allLabels = []
		allPredictions = []
		trainLabels = []
		trainPredictions = []
		valLabels = []
		valPredictions = []
		testLabels = []
		testPredictions = []
		
		for anInput in inputs_replicated:
			all_labels, all_predictions, train_labels, train_predictions, val_labels, val_predictions, test_labels, test_predictions = processItem(anInput)
			allLabels.append(all_labels)
			allPredictions.append(all_predictions)
			trainLabels.append(train_labels)
			trainPredictions.append(train_predictions)
			valLabels.append(val_labels)
			valPredictions.append(val_predictions)
			testLabels.append(test_labels)
			testPredictions.append(test_predictions)
			
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			allLabels = Replication.re_interlace(allLabels, inputs_flat)
			allPredictions = Replication.re_interlace(allPredictions, inputs_flat)
			trainLabels = Replication.re_interlace(trainLabels, inputs_flat)
			trainPredictions = Replication.re_interlace(trainPredictions, inputs_flat)
			valLabels = Replication.re_interlace(valLabels, inputs_flat)
			valPredictions = Replication.re_interlace(valPredictions, inputs_flat)
			testLabels = Replication.re_interlace(testLabels, inputs_flat)
			testPredictions = Replication.re_interlace(testPredictions, inputs_flat)
			
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			allLabels = Replication.unflatten(allLabels, match_list)
			allPredictions = Replication.unflatten(allPredictions, match_list)
			trainLabels = Replication.unflatten(trainLabels, match_list)
			trainPredictions = Replication.unflatten(trainPredictions, match_list)
			valLabels = Replication.unflatten(valLabels, match_list)
			valPredictions = Replication.unflatten(valPredictions, match_list)
			testLabels = Replication.unflatten(testLabels, match_list)
			testPredictions = Replication.unflatten(testPredictions, match_list)
			
		if len(allLabels) == 1:
			if isinstance(allLabels[0], list):
				allLabels = allLabels[0]
		self.outputs['All Labels'].sv_set([allLabels])
		if len(allPredictions) == 1:
			if isinstance(allPredictions[0], list):
				allPredictions = allPredictions[0]
		self.outputs['All Predictions'].sv_set([allPredictions])
		if len(trainLabels) == 1:
			if isinstance(trainLabels[0], list):
				trainLabels = trainLabels[0]
		self.outputs['Train Labels'].sv_set([trainLabels])
		if len(trainPredictions) == 1:
			if isinstance(trainPredictions[0], list):
				trainPredictions = trainPredictions[0]
		self.outputs['Train Predictions'].sv_set([trainPredictions])
		if len(valLabels) == 1:
			if isinstance(valLabels[0], list):
				valLabels = valLabels[0]
		self.outputs['Val Labels'].sv_set([valLabels])
		if len(valPredictions) == 1:
			if isinstance(valPredictions[0], list):
				valPredictions = valPredictions[0]
		self.outputs['Val Predictions'].sv_set([valPredictions])
		if len(testLabels) == 1:
			if isinstance(testLabels[0], list):
				testLabels = testLabels[0]
		self.outputs['Test Labels'].sv_set([testLabels])
		if len(testPredictions) == 1:
			if isinstance(testPredictions[0], list):
				testPredictions = testPredictions[0]
		self.outputs['Test Predictions'].sv_set([testPredictions])
		
	
def register():
	bpy.utils.register_class(SvDGLPredict_NC)

def unregister():
	bpy.utils.unregister_class(SvDGLPredict_NC)
