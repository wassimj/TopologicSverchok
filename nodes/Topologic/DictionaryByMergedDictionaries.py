import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

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

def getValueAtKey(item, key):
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

def getValues(item):
	keys = item.Keys()
	returnList = []
	for key in keys:
		try:
			attr = item.ValueAtKey(key)
		except:
			raise Exception("Dictionary.Values - Error: Could not retrieve a Value at the specified key ("+key+")")
		if isinstance(attr, topologic.IntAttribute):
			returnList.append(attr.IntValue())
		elif isinstance(attr, topologic.DoubleAttribute):
			returnList.append(attr.DoubleValue())
		elif isinstance(attr, topologic.StringAttribute):
			returnList.append(attr.StringValue())
		elif isinstance(attr, topologic.ListAttribute):
			returnList.append(listAttributeValues(attr))
		else:
			returnList.append("")
	return returnList

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("DictionaryByKeysValues - Keys and Values do not have the same length")
	stl_keys = []
	stl_values = []
	for i in range(len(keys)):
		if isinstance(keys[i], str):
			stl_keys.append(keys[i])
		else:
			stl_keys.append(str(keys[i]))
		if isinstance(values[i], list) and len(values[i]) == 1:
			value = values[i][0]
		else:
			value = values[i]
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
			raise Exception("Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
	myDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
	return myDict

def processItem(sources):
	sinkKeys = []
	sinkValues = []
	d = sources[0]
	if d != None:
		stlKeys = d.Keys()
		if len(stlKeys) > 0:
			sinkKeys = d.Keys()
			sinkValues = getValues(d)
		for i in range(1,len(sources)):
			d = sources[i]
			if d == None:
				continue
			stlKeys = d.Keys()
			if len(stlKeys) > 0:
				sourceKeys = d.Keys()
				for aSourceKey in sourceKeys:
					if aSourceKey not in sinkKeys:
						sinkKeys.append(aSourceKey)
						sinkValues.append("")
				for i in range(len(sourceKeys)):
					index = sinkKeys.index(sourceKeys[i])
					sourceValue = getValueAtKey(d,sourceKeys[i])
					if sourceValue != None:
						if sinkValues[index] != "":
							if isinstance(sinkValues[index], list):
								sinkValues[index].append(sourceValue)
							else:
								sinkValues[index] = [sinkValues[index], sourceValue]
						else:
							sinkValues[index] = sourceValue
	if len(sinkKeys) > 0 and len(sinkValues) > 0:
		newDict = processKeysValues(sinkKeys, sinkValues)
		return newDict
	return None

class SvDictionaryByMergedDictionaries(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Dictionary by merging a list of input Dictionaries   
	"""
	bl_idname = 'SvDictionaryByMergedDictionaries'
	bl_label = 'Dictionary.ByMergedDictionaries'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Dictionaries')
		self.outputs.new('SvStringsSocket', 'Dictionary')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		dictList = self.inputs['Dictionaries'].sv_get(deepcopy=True)
		outputs = []
		for aList in dictList:
			outputs.append(processItem(aList))
		self.outputs['Dictionary'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDictionaryByMergedDictionaries)

def unregister():
	bpy.utils.unregister_class(SvDictionaryByMergedDictionaries)
