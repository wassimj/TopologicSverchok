import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

#from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
from topologic import Dictionary, IntAttribute, DoubleAttribute, StringAttribute, ListAttribute
from . import Replication

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

def processItem(item):
	d, key = item
	try:
		if isinstance(d, dict):
			attr = d[key]
		elif isinstance(d, Dictionary):
			attr = d.ValueAtKey(key)
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
	elif isinstance(attr, float) or isinstance(attr, int) or isinstance(attr, str):
		return attr
	elif isinstance(attr, list):
		return listAttributeValues(attr)
	elif isinstance(attr, dict):
		return attr
	else:
		return None

class SvDictionaryValueAtKey(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: outputs the value from the input Dictionary associated with the input key   
	"""
	bl_idname = 'SvDictionaryValueAtKey'
	bl_label = 'Dictionary.ValueAtKey'
	Key: StringProperty(name="Key", update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Dictionary')
		self.inputs.new('SvStringsSocket', 'Key').prop_name='Key'
		self.outputs.new('SvStringsSocket', 'Value')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		
		DictionaryList = Replication.flatten(self.inputs['Dictionary'].sv_get(deepcopy=True))
		key = Replication.flatten(self.inputs['Key'].sv_get(deepcopy=True))[0]
		outputs = []
		for aDict in DictionaryList:
			outputs.append(processItem([aDict, key]))
		self.outputs['Value'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDictionaryValueAtKey)

def unregister():
	bpy.utils.unregister_class(SvDictionaryValueAtKey)
