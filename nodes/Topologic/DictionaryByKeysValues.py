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
		keyLists = self.inputs['Keys'].sv_get(deepcopy=False)
		valueLists = self.inputs['Values'].sv_get(deepcopy=False)
		if isinstance(keyLists[0], list) == False:
			keyLists = [keyLists]
		if isinstance(valueLists[0], list) == False:
			valueLists = [valueLists]
		dictionaries = []
		if len(keyLists) != len(valueLists):
			return
		for i in range(len(keyLists)):
			if len(keyLists[i]) != len(valueLists[i]):
				return
			stl_keys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
			stl_values = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
			for j in range(len(keyLists[i])):
				stl_keys.push_back(keyLists[i][j])
				stl_values.push_back(topologic.StringAttribute(valueLists[i][j]))
			dictionaries.append(topologic.Dictionary.ByKeysValues(stl_keys, stl_values))
		self.outputs['Dictionary'].sv_set(dictionaries)

def register():
	bpy.utils.register_class(SvDictionaryByKeysValues)

def unregister():
	bpy.utils.unregister_class(SvDictionaryByKeysValues)
