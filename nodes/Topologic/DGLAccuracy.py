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
	mask = []
	for i in range(len(dgl_predictions)):
		if dgl_predictions[i] == dgl_labels[i]:
			num_correct = num_correct + 1
			mask.append(True)
		else:
			mask.append(False)
	size = len(dgl_predictions)
	return [size, num_correct, len(dgl_predictions)- num_correct, mask, num_correct / len(dgl_predictions)]

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
		self.outputs.new('SvStringsSocket', 'Mask')
		self.outputs.new('SvStringsSocket', 'Accuracy')
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
			inputs_flat.append(inp)
		inputs_replicated = Replication.replicateInputs(inputs_flat, self.Replication)
		sizeList = []
		correctList = []
		wrongList = []
		maskList = []
		accuracyList = []
		for anInput in inputs_replicated:
			size, correct, wrong, mask, accuracy =  processItem(anInput)
			sizeList.append(size)
			correctList.append(correct)
			wrongList.append(wrong)
			maskList.append(mask)
			accuracyList.append(accuracy)
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			sizeList = Replication.re_interlace(sizeList, inputs_flat)
			correctList = Replication.re_interlace(correctList, inputs_flat)
			wrongList = Replication.re_interlace(wrongList, inputs_flat)
			maskList = Replication.re_interlace(maskList, inputs_flat)
			accuracyList = Replication.re_interlace(accuracyList, inputs_flat)
		'''
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			sizeList = Replication.unflatten(sizeList, match_list)
			correctList = Replication.unflatten(correctList, match_list)
			wrongList = Replication.unflatten(wrongList, match_list)
			maskList = Replication.unflatten(maskList, match_list)
			accuracyList = Replication.unflatten(accuracyList, match_list)
		'''
		if len(sizeList) == 1:
			if isinstance(sizeList[0], list):
				sizeList = sizeList[0]
		if len(correctList) == 1:
			if isinstance(correctList[0], list):
				correctList = correctList[0]
		if len(wrongList) == 1:
			if isinstance(wrongList[0], list):
				wrongList = wrongList[0]
		if len(maskList) == 1:
			if isinstance(maskList[0], list):
				maskList = maskList[0]
		if len(accuracyList) == 1:
			if isinstance(accuracyList[0], list):
				accuracyList = accuracyList[0]

		self.outputs['Size'].sv_set([sizeList])
		self.outputs['Correct'].sv_set([correctList])
		self.outputs['Wrong'].sv_set([wrongList])
		self.outputs['Mask'].sv_set([maskList])
		self.outputs['Accuracy'].sv_set([accuracyList])

def register():
	bpy.utils.register_class(SvDGLAccuracy)

def unregister():
	bpy.utils.unregister_class(SvDGLAccuracy)
