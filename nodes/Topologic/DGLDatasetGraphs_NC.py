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

def processItem(item):
	dataset = item
	try:
		_ = dataset[1]
	except:
		dataset = [dataset[0]]
	graphs = []
	for aGraph in dataset:
		if isinstance(aGraph, tuple):
			aGraph = aGraph[0]
		graphs.append(aGraph)
	return graphs

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem(input)
	return output

class SvDGLDatasetGraphs_NC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Returns the DGL Graphs found in the input DGL Dataset
	"""
	bl_idname = 'SvDGLDatasetGraphs_NC'
	bl_label = 'DGL.DatasetGraphs_NC'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'DGL Dataset')
		self.outputs.new('SvStringsSocket', 'DGL Graphs')
		self.width = 200
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		input = self.inputs[0].sv_get(deepcopy=False)
		output = recur(input)
		if not isinstance(output, list):
			output = [output]
		self.outputs['DGL Graphs'].sv_set(output)

def register():
	bpy.utils.register_class(SvDGLDatasetGraphs_NC)

def unregister():
	bpy.utils.unregister_class(SvDGLDatasetGraphs_NC)
