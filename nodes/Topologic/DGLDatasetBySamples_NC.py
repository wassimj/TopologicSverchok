import sys
sys.path.append(r"D:\Anaconda3\envs\py310\Lib\site-packages")
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import dgl.data

from . import Replication

samples = [("Cora", "Cora", "", 1)]

def processItem(item):
	sample = item
	if sample == 'Cora':
		return dgl.data.CoraGraphDataset()
	else:
		raise NotImplementedError

class SvDGLDatasetBySamples_NC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a DGL Dataset by DGL Samples
	"""
	bl_idname = 'SvDGLDatasetBySamples_NC'
	bl_label = 'DGL.DatasetBySamples_NC'
	SamplesProp: EnumProperty(name="Samples", description="Choose a sample dataset", default="Cora", items=samples, update=updateNode)

	def sv_init(self, context):
		self.width=200
		self.inputs.new('SvStringsSocket', 'Sample').prop_name="SamplesProp"
		self.outputs.new('SvStringsSocket', 'DGL Dataset')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		sampleList = self.inputs['Sample'].sv_get(deepcopy=True)
		sampleList = Replication.flatten(sampleList)
		outputs = []
		for anInput in sampleList:
			outputs.append(processItem(anInput))
		self.outputs['DGL Dataset'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDGLDatasetBySamples_NC)

def unregister():
	bpy.utils.unregister_class(SvDGLDatasetBySamples_NC)
