import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
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

def getKeys(item):
	stl_keys = item.Keys()
	returnList = []
	copyKeys = stl_keys.__class__(stl_keys) #wlav suggested workaround. Make a copy first
	for x in copyKeys:
		k = x.c_str()
		returnList.append(k)
	return returnList

def getValues(item):
	keys = getKeys(item)
	returnList = []
	fv = None
	for key in keys:
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
		returnList.append(fv)
	return returnList

def processItem(sources):
	sinkKeys = []
	sinkValues = []
	d = sources[0]
	if d != None:
		stlKeys = d.Keys()
		if len(stlKeys) > 0:
			sinkKeys = getKeys(d)
			sinkValues = getValues(d)
	for i in range(1,len(sources)):
		d = sources[i]
		if d == None:
			continue
		stlKeys = d.Keys()
		if len(stlKeys) > 0:
			sourceKeys = getKeys(d)
			for aSourceKey in sourceKeys:
				if aSourceKey not in sinkKeys:
					sinkKeys.append(aSourceKey)
					sinkValues.append("")
			for i in range(len(sourceKeys)):
				index = sinkKeys.index(sourceKeys[i])
				k = cppyy.gbl.std.string(sourceKeys[i])
				sourceValue = d.ValueAtKey(k).Value()
				if sourceValue != None:
					if sinkValues[index] != "":
						if isinstance(sinkValues[index], list):
							sinkValues[index].append(sourceValue)
						else:
							sinkValues[index] = [sinkValues[index], sourceValue]
					else:
						sinkValues[index] = sourceValue
	if len(sinkKeys) > 0 and len(sinkValues) > 0:
		stlKeys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
		for sinkKey in sinkKeys:
			stlKeys.push_back(sinkKey)
		stlValues = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
		for sinkValue in sinkValues:
			if isinstance(sinkValue, bool):
				stlValues.push_back(topologic.IntAttribute(sinkValue))
			elif isinstance(sinkValue, int):
				stlValues.push_back(topologic.IntAttribute(sinkValue))
			elif isinstance(sinkValue, float):
				stlValues.push_back(topologic.DoubleAttribute(sinkValue))
			elif isinstance(sinkValue, str):
				stlValues.push_back(topologic.StringAttribute(sinkValue))
			elif isinstance(sinkValue, list):
				l = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
				for v in sinkValue:
					if isinstance(v, bool):
						l.push_back(topologic.IntAttribute(v))
					elif isinstance(v, int):
						l.push_back(topologic.IntAttribute(v))
					elif isinstance(v, float):
						l.push_back(topologic.DoubleAttribute(v))
					elif isinstance(v, str):
						l.push_back(topologic.StringAttribute(v))
				stlValues.push_back(topologic.ListAttribute(l))
		newDict = topologic.Dictionary.ByKeysValues(stlKeys, stlValues)
		return newDict

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
		dictList = flatten(dictList)
		outputs = []
		outputs.append(processItem(dictList))
		self.outputs['Dictionary'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDictionaryByMergedDictionaries)

def unregister():
	bpy.utils.unregister_class(SvDictionaryByMergedDictionaries)
