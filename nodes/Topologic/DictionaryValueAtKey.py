import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

#from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
from topologic import Dictionary, IntAttribute, DoubleAttribute, StringAttribute, ListAttribute

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
	return returnList

def processItem(item, key):
	try:
		attr = item.ValueAtKey(key)
	except:
		raise Exception("Dictionary.ValueAtKey - Error: Could not retrieve a Value at the specified key ("+key+")")
	if isinstance(attr, IntAttribute):
		return (attr.IntValue())
	elif isinstance(attr, DoubleAttribute):
		return (attr.DoubleValue())
	elif isinstance(attr, StringAttribute):
		return (attr.StringValue())
	elif isinstance(attr, ListAttribute):
		return (listAttributeValues(attr))
	else:
		return None

class SvDictionaryValueAtKey(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: outputs the value from the input Dictionary associated with the input key   
	"""
	bl_idname = 'SvDictionaryValueAtKey'
	bl_label = 'Dictionary.ValueAtKey'
	Keys: StringProperty(name="Keys", update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Dictionary')
		self.inputs.new('SvStringsSocket', 'Key').prop_name='Keys'
		self.outputs.new('SvStringsSocket', 'Value')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		
		DictionaryList = flatten(self.inputs['Dictionary'].sv_get(deepcopy=True))
		key = flatten(self.inputs['Key'].sv_get(deepcopy=True))[0]
		outputs = []
		for aDict in DictionaryList:
			outputs.append(processItem(aDict, key))
		self.outputs['Value'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDictionaryValueAtKey)

def unregister():
	bpy.utils.unregister_class(SvDictionaryValueAtKey)
