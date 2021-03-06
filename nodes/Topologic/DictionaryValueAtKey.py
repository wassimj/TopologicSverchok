import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
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

def processItem(dict, item):
	stl_keys = dict.Keys()
	keyList = []
	returnValue = None
	for aKey in stl_keys:
		keyList.append(aKey.c_str())
	if item in keyList:
		value = dict.ValueAtKey(item)
		s = cppyy.bind_object(value.Value(), 'StringStruct')
		returnValue = str(s.getString)
	return returnValue

def recur(dict, input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(dict, anItem))
	else:
		output = processItem(dict, input)
	return output

class SvDictionaryValueAtKey(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Return the value from the input Dictionary associated with the input key   
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
		
		DictionaryList = flatten(self.inputs['Dictionary'].sv_get(deepcopy=False))
		inputs = self.inputs['Key'].sv_get(deepcopy=False)
		outputs = []
		for aDict in DictionaryList:
			outputList = []
			for anInput in inputs:
				outputList.append(recur(aDict, anInput))
			outputs.append(outputList)
		if len(outputs) == 1:
			outputs = outputs[0]
		self.outputs['Value'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDictionaryValueAtKey)

def unregister():
	bpy.utils.unregister_class(SvDictionaryValueAtKey)
