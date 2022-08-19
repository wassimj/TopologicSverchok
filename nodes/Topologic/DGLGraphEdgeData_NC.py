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
	return item.edata

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

class SvDGLGraphEdgeData_NC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Returns the edge data of the input DGL Graph
	"""
	bl_idname = 'SvDGLGraphEdgeData_NC'
	bl_label = 'DGL.GraphEdgeData_NC'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'DGL Graph')
		self.outputs.new('SvStringsSocket', 'Edge Data')
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
		self.outputs['Edge Data'].sv_set(output)

def register():
	bpy.utils.register_class(SvDGLGraphEdgeData_NC)

def unregister():
	bpy.utils.unregister_class(SvDGLGraphEdgeData_NC)
