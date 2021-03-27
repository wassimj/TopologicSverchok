import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

class SvDictionaryByKeysValues(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Dictionary from a list of keys and values   
	"""
	bl_idname = 'SvDictionaryByKeysValues'
	bl_label = 'Dictionary.ByKeysValues'
	Keys: StringProperty(name="Keys", update=updateNode)
	Values: StringProperty(name="Values", update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Keys').prop_name='Keys'
		self.inputs.new('SvStringsSocket', 'Values').prop_name='Values'
		self.outputs.new('SvStringsSocket', 'Dictionary')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		keyList = self.inputs['Keys'].sv_get(deepcopy=False)
		valueList = self.inputs['Values'].sv_get(deepcopy=False)
		keyList = flatten(keyList)
		valueList = flatten(valueList)
		if(len(keyList) == 0 or len(valueList) == 0):
			return
		if(len(keyList) > len(valueList)):
			keyList = keyList[:len(valueList)]
		elif(len(valueList) > len(keyList)):
			valueList = valueList[:len(keyList)]
		keys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
		values = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
		for i in range(len(keyList)):
			keys.push_back(keyList[i])
			values.push_back(topologic.StringAttribute(valueList[i]))
		dictionary = topologic.Dictionary.ByKeysValues(keys, values)
		self.outputs['Dictionary'].sv_set([dictionary])

def register():
	bpy.utils.register_class(SvDictionaryByKeysValues)

def unregister():
	bpy.utils.unregister_class(SvDictionaryByKeysValues)
