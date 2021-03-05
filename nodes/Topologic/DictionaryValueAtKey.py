import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
import cppyy
from cppyy.gbl.std import string, list
		
class SvDictionaryValueAtKey(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Dictionary from a list of keys and values   
	"""
	bl_idname = 'SvDictionaryValueAtKey'
	bl_label = 'Dictionary.ValueAtKey'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Dictionary')
		self.inputs.new('SvStringsSocket', 'Key')
		self.outputs.new('SvStringsSocket', 'Value')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		
		DictionaryList = self.inputs['Dictionary'].sv_get(deepcopy=False)
		keys = self.inputs['Key'].sv_get(deepcopy=True)
		values = []
		for i in range(len(DictionaryList)):
			key = string(keys[i][0])
			value = DictionaryList[i][0].ValueAtKey(key)
			s = cppyy.bind_object(value.Value(), 'StringStruct')
			values.append(s.getString)
		self.outputs['Value'].sv_set(values)

def register():
	bpy.utils.register_class(SvDictionaryValueAtKey)

def unregister():
	bpy.utils.unregister_class(SvDictionaryValueAtKey)
