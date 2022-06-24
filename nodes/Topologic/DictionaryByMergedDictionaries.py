import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication
from . import DictionaryByKeysValues, DictionaryValues, DictionaryValueAtKey

def processItem(sources):
	sinkKeys = []
	sinkValues = []
	d = sources[0]
	if d != None:
		stlKeys = d.Keys()
		if len(stlKeys) > 0:
			sinkKeys = d.Keys()
			sinkValues = DictionaryValues.processItem(d)
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
					sourceValue = DictionaryValueAtKey.processItem([d,sourceKeys[i]])
					if sourceValue != None:
						if sinkValues[index] != "":
							if isinstance(sinkValues[index], list):
								sinkValues[index].append(sourceValue)
							else:
								sinkValues[index] = [sinkValues[index], sourceValue]
						else:
							sinkValues[index] = sourceValue
	if len(sinkKeys) > 0 and len(sinkValues) > 0:
		newDict = DictionaryByKeysValues.processItem([sinkKeys, sinkValues])
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
		dictList = Replication.flatten(dictList)
		outputs = []
		outputs.append(processItem(dictList))
		self.outputs['Dictionary'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDictionaryByMergedDictionaries)

def unregister():
	bpy.utils.unregister_class(SvDictionaryByMergedDictionaries)
