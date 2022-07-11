import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from . import Replication
import os
from os.path import expanduser

def processItem(filePath):
	os.system("start "+filePath)
	return True

class SvTopologicOpenFilePath(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Opens the input file path
	"""
	
	bl_idname = 'SvTopologicOpenFilePath'
	bl_label = 'Topologic.OpenFilePath'
	FilePathProp: StringProperty(name="File Path", description="File Path to open.", update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvFilePathSocket', 'File Path').prop_name='FilePathProp'
		self.outputs.new('SvStringsSocket', 'Status')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return

		filePathList = self.inputs['File Path'].sv_get(deepcopy=True)
		filePathList = Replication.flatten(filePathList)
		outputs = []
		for anInput in filePathList:
			outputs.append(processItem(anInput))
		self.outputs['Status'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologicOpenFilePath)

def unregister():
	bpy.utils.unregister_class(SvTopologicOpenFilePath)
