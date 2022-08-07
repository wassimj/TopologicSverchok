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
	graphs_folder_path = item
	return dgl.data.CSVDataset(graphs_folder_path, force_reload=True)

class SvDGLDatasetByImportedCSV_NC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a DGL Dataset by Imported CSV FILE for Node Classification
	"""
	bl_idname = 'SvDGLDatasetByImportedCSV_NC'
	bl_label = 'DGL.DatasetByImportedCSV_NC'
	GraphsFolderPathProp: StringProperty(name="Graphs Folder Path", description="The folder path to the Graphs CSV files", update=updateNode)

	def sv_init(self, context):
		self.width=200
		self.inputs.new('SvFilePathSocket', 'Graphs Folder Path').prop_name = 'GraphsFolderPathProp'
		self.outputs.new('SvStringsSocket', 'DGL Dataset')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		graphsFolderPathList = self.inputs['Graphs Folder Path'].sv_get(deepcopy=False)

		graphsFolderPathList = Replication.flatten(graphsFolderPathList)
		outputs = []
		for anInput in graphsFolderPathList:
			outputs.append(processItem(anInput))
		self.outputs['DGL Dataset'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDGLDatasetByImportedCSV_NC)

def unregister():
	bpy.utils.unregister_class(SvDGLDatasetByImportedCSV_NC)
