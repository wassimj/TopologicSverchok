import sys
sys.path.append(r"D:\Anaconda3\envs\py310\Lib\site-packages")
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import dgl
import pickle
import topologic
from dgl.data import DGLDataset
import torch
import numpy as np

from . import Replication

def processItem(item):
	dgl_labels, dgl_predictions = item
	
	num_correct = 0
	for i in range(len(dgl_predictions)):
		if dgl_predictions[i] == dgl_labels[i]:
			num_correct = num_correct + 1
	size = len(dgl_predictions)
	return [size, num_correct, len(dgl_predictions)- num_correct, num_correct / len(dgl_predictions)]

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDGLAccuracy(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the accuracy of the input predictions based on the input labels
	"""
	bl_idname = 'SvDGLAccuracy'
	bl_label = 'DGL.Accuracy'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	LabelProp: IntProperty(name='Label', description='The actual label of the graph', default=0, update=updateNode)
	PredictionProp: IntProperty(name='Prediction', description='The predicted label of the graph', default=0, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Label').prop_name='LabelProp'
		self.inputs.new('SvStringsSocket', 'Prediction').prop_name='PredictionProp'
		self.outputs.new('SvStringsSocket', 'Size')
		self.outputs.new('SvStringsSocket', 'Correct')
		self.outputs.new('SvStringsSocket', 'Wrong')
		self.outputs.new('SvStringsSocket', 'Accuracy')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Accuracy'].sv_set([])
			return
		labelList = self.inputs['Label'].sv_get(deepcopy=True)
		predictionList = self.inputs['Prediction'].sv_get(deepcopy=True)
		inputs = [labelList, predictionList]
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
		sizeList = []
		correctList = []
		wrongList = []
		accuracyList = []
		for anInput in inputs:
			size, correct, wrong, accuracy =  processItem(anInput)
			sizeList.append(size)
			correctList.append(correct)
			wrongList.append(wrong)
			accuracyList.append(accuracy)
		self.outputs['Size'].sv_set(sizeList)
		self.outputs['Correct'].sv_set(correctList)
		self.outputs['Wrong'].sv_set(wrongList)
		self.outputs['Accuracy'].sv_set(accuracyList)

def register():
	bpy.utils.register_class(SvDGLAccuracy)

def unregister():
	bpy.utils.unregister_class(SvDGLAccuracy)
