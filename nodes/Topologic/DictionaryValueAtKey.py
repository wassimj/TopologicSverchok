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

def processItem(item, key):
	fv = None
	try:
		v = item.ValueAtKey(key).Value()
	except:
		raise Exception("Error: Could not retrieve a Value at the specified key ("+key+")")
	if (isinstance(v, int) or (isinstance(v, float))):
		fv = v
	elif (isinstance(v, cppyy.gbl.std.string)):
		fv = v.c_str()
	else:
		resultList = []
		for i in v:
			if isinstance(i.Value(), cppyy.gbl.std.string):
				resultList.append(i.Value().c_str())
			else:
				resultList.append(i.Value())
		fv = resultList
	return fv


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
