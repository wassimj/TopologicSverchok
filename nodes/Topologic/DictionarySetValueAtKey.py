import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

#from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
from topologic import Dictionary, IntAttribute, DoubleAttribute, StringAttribute, ListAttribute

from . import DictionaryByKeysValues, DictionaryValueAtKey

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def listAttributeValues(listAttribute):
	listAttributes = listAttribute.ListValue()
	returnList = []
	for attr in listAttributes:
		if isinstance(attr, IntAttribute):
			returnList.append(attr.IntValue())
		elif isinstance(attr, DoubleAttribute):
			returnList.append(attr.DoubleValue())
		elif isinstance(attr, StringAttribute):
			returnList.append(attr.StringValue())
		elif isinstance(attr, float) or isinstance(attr, int) or isinstance(attr, str) or isinstance(attr, dict):
			returnList.append(attr)
	return returnList

def processPythonDictionary (item, key, value):
	item[key] = value
	return item

def processTopologicDictionary(item, key, value):
	keys = item.Keys()
	if not key in keys:
		keys.append(key)
	values = []
	for k in keys:
		if k == key:
			values.append(value)
		else:
			values.append(DictionaryValueAtKey.processItem([item, k]))
	return DictionaryByKeysValues.processKeysValues(keys, values)

def processItem(item, key, value):
	if isinstance(item, dict):
		return processPythonDictionary(item, key, value)
	elif isinstance(item, Dictionary):
		return processTopologicDictionary(item, key, value)
	else:
		raise Exception("Dictionary.SetValueAtKey - Error: Input is not a dictionary")

class SvDictionarySetValueAtKey(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: sets the value associated with the input key to the input dictionary
	"""
	bl_idname = 'SvDictionarySetValueAtKey'
	bl_label = 'Dictionary.SetValueAtKey'
	Key: StringProperty(name="Key", update=updateNode)
	Value: StringProperty(name="Value", update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Dictionary')
		self.inputs.new('SvStringsSocket', 'Key').prop_name='Key'
		self.inputs.new('SvStringsSocket', 'Value').prop_name='Value'
		self.outputs.new('SvStringsSocket', 'Dictionary')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		
		DictionaryList = flatten(self.inputs['Dictionary'].sv_get(deepcopy=True))
		key = flatten(self.inputs['Key'].sv_get(deepcopy=True))[0]
		value = flatten(self.inputs['Value'].sv_get(deepcopy=True))[0]
		outputs = []
		for aDict in DictionaryList:
			outputs.append(processItem(aDict, key, value))
		self.outputs['Dictionary'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDictionarySetValueAtKey)

def unregister():
	bpy.utils.unregister_class(SvDictionarySetValueAtKey)
