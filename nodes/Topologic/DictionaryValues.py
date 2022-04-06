import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Dictionary, IntAttribute, DoubleAttribute, StringAttribute, ListAttribute

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
		elif isinstance(attr, float) or isinstance(attr, int) or isinstance(attr, str):
			returnList.append(attr)
	return returnList

def processItem(item):
	if isinstance(item, dict):
		keys = item.keys()
	elif isinstance(item, Dictionary):
		keys = item.Keys()
	returnList = []
	for key in keys:
		try:
			if isinstance(item, dict):
				attr = item[key]
			elif isinstance(item, Dictionary):
				attr = item.ValueAtKey(key)
			else:
				attr = None
		except:
			raise Exception("Dictionary.Values - Error: Could not retrieve a Value at the specified key ("+key+")")
		if isinstance(attr, IntAttribute):
			returnList.append(attr.IntValue())
		elif isinstance(attr, DoubleAttribute):
			returnList.append(attr.DoubleValue())
		elif isinstance(attr, StringAttribute):
			returnList.append(attr.StringValue())
		elif isinstance(attr, ListAttribute):
			returnList.append(listAttributeValues(attr))
		elif isinstance(attr, float) or isinstance(attr, int) or isinstance(attr, str):
			returnList.append(attr)
		elif isinstance(attr, list):
			returnList.append(listAttributeValues(attr))
		else:
			returnList.append("")
	return returnList

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem(input)
	return output
	
class SvDictionaryValues(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the list of values of the input Dictionary   
	"""
	bl_idname = 'SvDictionaryValues'
	bl_label = 'Dictionary.Values'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Dictionary')
		self.outputs.new('SvStringsSocket', 'Values')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		
		inputs = self.inputs['Dictionary'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		if len(outputs) == 1:
			outputs = outputs[0]
		self.outputs['Values'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDictionaryValues)

def unregister():
	bpy.utils.unregister_class(SvDictionaryValues)
