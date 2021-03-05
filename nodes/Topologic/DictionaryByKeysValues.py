import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy
		
class SvDictionaryByKeysValues(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Dictionary from a list of keys and values   
	"""
	bl_idname = 'SvDictionaryByKeysValues'
	bl_label = 'Dictionary.ByKeysValues'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Keys')
		self.inputs.new('SvStringsSocket', 'Values')
		self.outputs.new('SvStringsSocket', 'Dictionary')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		
		keyList = self.inputs['Keys'].sv_get(deepcopy=False)
		valueList = self.inputs['Values'].sv_get(deepcopy=False)
		if(len(keyList) > len(valueList)):
			keyList = keyList[:len(valueList)]
		elif(len(valueList) > len(keyList)):
			valueList = valueList[:len(keyList)]
		print(keyList)
		print(valueList)
		keys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
		values = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
		dictionaries = []
		for i in range(len(keyList)):
			if isinstance(keyList[i], list) == False:
				keyList[i] = [keyList[i]]
			keys.push_back(cppyy.gbl.std.string(keyList[i][0]))
			if isinstance(valueList[i], list) == False:
				valueList[i] = [valueList[i]]
			value = topologic.StringAttribute(valueList[i][0])
			values.push_back(value)
		dictionary = topologic.Dictionary.ByKeysValues(keys, values)
		self.outputs['Dictionary'].sv_set([[dictionary]])

def register():
	bpy.utils.register_class(SvDictionaryByKeysValues)

def unregister():
	bpy.utils.unregister_class(SvDictionaryByKeysValues)
