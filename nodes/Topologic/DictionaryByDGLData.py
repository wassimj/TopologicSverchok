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
from . import DictionaryByKeysValues
def processItem(item):
	keys = list(item.keys())
	vList = []
	for k in keys:
		vList.append(item[k].tolist())
	dictionaries = []
	for v in range(len(vList[0])):
		values = []
		for k in range(len(keys)):
			value = vList[k][v]
			values.append(value)
		dictionaries.append(DictionaryByKeysValues.processItem([keys, values]))
	return dictionaries

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

class SvDictionaryByDGLData(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Returns the edge data of the input DGL Graph
	"""
	bl_idname = 'SvDictionaryByDGLData'
	bl_label = 'Dictionary.ByDGLData'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'DGL Data')
		self.outputs.new('SvStringsSocket', 'Dictionary')
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
		self.outputs['Dictionary'].sv_set(output)

def register():
	bpy.utils.register_class(SvDictionaryByDGLData)

def unregister():
	bpy.utils.unregister_class(SvDictionaryByDGLData)
