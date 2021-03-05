import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
import cppyy
from cppyy.gbl.std import string, list
		
class SvDictionaryKeys(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the list of keys of the input Dictionary   
	"""
	bl_idname = 'SvDictionaryKeys'
	bl_label = 'Dictionary.Keys'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Dictionary')
		self.outputs.new('SvStringsSocket', 'Keys')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		
		DictionaryList = self.inputs['Dictionary'].sv_get(deepcopy=True)
		output = []
		for i in range(len(DictionaryList)):
			keys = DictionaryList[i][0].Keys()
			py_keys = []
			for aKey in keys:
				py_keys.append(str(aKey))
			output.append(py_keys)
		self.outputs['Keys'].sv_set(output)

def register():
	bpy.utils.register_class(SvDictionaryKeys)

def unregister():
	bpy.utils.unregister_class(SvDictionaryKeys)
