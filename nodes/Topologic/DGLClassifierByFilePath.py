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

	Returns
	-------
	The classifier model

	"""
	return torch.load(item)

class SvDGLClassifierByFilePath(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the model saved at the input file path
	"""
	
	bl_idname = 'SvDGLClassifierByFilePath'
	bl_label = 'DGL.ClassifierByFilePath'
	FilePathProp: StringProperty(name="File Path", description="Path from which to load the classifier.", update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvFilePathSocket', 'File Path').prop_name='FilePathProp'
		self.outputs.new('SvStringsSocket', 'Classifier')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return

		filePathList = self.inputs['File Path'].sv_get(deepcopy=True)
		filePathList = Replication.flatten(filePathList)
		outputs = []
		for anInput in filePathList:
			outputs.append(processItem(anInput))
		self.outputs['Classifier'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDGLClassifierByFilePath)

def unregister():
	bpy.utils.unregister_class(SvDGLClassifierByFilePath)
