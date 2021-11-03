import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import idprop

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import time

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
		if isinstance(attr, topologic.IntAttribute):
			returnList.append(attr.IntValue())
		elif isinstance(attr, topologic.DoubleAttribute):
			returnList.append(attr.DoubleValue())
		elif isinstance(attr, topologic.StringAttribute):
			returnList.append(attr.StringValue())
	return returnList

def valueAtKey(item, key):
	try:
		attr = item.ValueAtKey(key)
	except:
		raise Exception("Dictionary.ValueAtKey - Error: Could not retrieve a Value at the specified key ("+key+")")
	if isinstance(attr, topologic.IntAttribute):
		return (attr.IntValue())
	elif isinstance(attr, topologic.DoubleAttribute):
		return (attr.DoubleValue())
	elif isinstance(attr, topologic.StringAttribute):
		return (attr.StringValue())
	elif isinstance(attr, topologic.ListAttribute):
		return (listAttributeValues(attr))
	else:
		return None

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("DictionaryByKeysValues - Keys and Values do not have the same length")
	stl_keys = []
	stl_values = []
	for i in range(len(keys)):
		if keys[i] in '_RNA_UI':
			continue
		if isinstance(keys[i], str):
			stl_keys.append(keys[i])
		else:
			stl_keys.append(str(keys[i]))
		if isinstance(values[i], list) and len(values[i]) == 1:
			value = values[i][0]
		else:
			value = values[i]
		if isinstance(value, idprop.types.IDPropertyArray):
			value = value.to_list()
		if isinstance(value, bool):
			if value == False:
				stl_values.append(topologic.IntAttribute(0))
			else:
				stl_values.append(topologic.IntAttribute(1))
		elif isinstance(value, int):
			stl_values.append(topologic.IntAttribute(value))
		elif isinstance(value, float):
			stl_values.append(topologic.DoubleAttribute(value))
		elif isinstance(value, str):
			stl_values.append(topologic.StringAttribute(value))
		elif isinstance(value, list):
			l = []
			for v in value:
				if isinstance(v, bool):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, int):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, float):
					l.append(topologic.DoubleAttribute(v))
				elif isinstance(v, str):
					l.append(topologic.StringAttribute(v))
			stl_values.append(topologic.ListAttribute(l))
		else:
			stl_values.append(topologic.StringAttribute(str(value)))
	myDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
	return myDict

def processItem(source):
	keys = source.keys()
	if len(keys) < 1:
		raise Exception("DictionaryByCustomProperties - Error: The source has no custom properties")
	values = []
	for aKey in keys:
		value = source[aKey]
		values.append(source[aKey])
	return processKeysValues(keys, values)

class SvDictionaryByCustomProperties(bpy.types.Node, SverchCustomTreeNode):

	"""
	Triggers: Topologic
	Tooltip: Creates a dictionary from the custom properties of the input Blender Object
	"""
	bl_idname = 'SvDictionaryByCustomProperties'
	bl_label = 'Dictionary.ByCustomProperties'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Source')
		self.outputs.new('SvStringsSocket', 'Dictionary')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Dictionary'].sv_set([])
			return
		sourceList = self.inputs['Source'].sv_get(deepcopy=True)
		sourceList = flatten(sourceList)
		outputs = []
		for anInput in sourceList:
			outputs.append(processItem(anInput))
		self.outputs['Dictionary'].sv_set(outputs)
		end = time.time()
		print("Dictionary.ByCustomProperties Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvDictionaryByCustomProperties)

def unregister():
    bpy.utils.unregister_class(SvDictionaryByCustomProperties)
