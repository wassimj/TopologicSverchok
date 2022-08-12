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
	classifier, dataset  = item
	predictions = []
	labels = []
	if dataset.name == "cora_v2":
		g = dataset[0]
	else:
		g = dataset[0][0]
	features = g.ndata['feat']
	labels.append(g.ndata['label'].tolist())
	# Forward
	logits = classifier(g, features)
	# Compute prediction
	pred = logits.argmax(1).tolist()
	predictions.append(pred)
	return [Replication.flatten(labels), Replication.flatten(predictions)]

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
		self.outputs.new('SvStringsSocket', 'Labels')
		self.outputs.new('SvStringsSocket', 'Predictions')
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
		labels = []
		predictions = []
		for anInput in inputs_replicated:
			label, prediction = processItem(anInput)
			labels.append(label)
			predictions.append(prediction)
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			labels = Replication.re_interlace(labels, inputs_flat)
			predictions = Replication.re_interlace(predictions, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			labels = Replication.unflatten(labels, match_list)
			predictions = Replication.unflatten(predictions, match_list)
		if len(labels) == 1:
			if isinstance(labels[0], list):
				labels = labels[0]
		if len(predictions) == 1:
			if isinstance(predictions[0], list):
				predictions = predictions[0]
		self.outputs['Labels'].sv_set([labels])
		self.outputs['Predictions'].sv_set([predictions])

def register():
	bpy.utils.register_class(SvDGLPredict_NC)

def unregister():
	bpy.utils.unregister_class(SvDGLPredict_NC)
