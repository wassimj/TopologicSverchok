import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def getKeys(item):
	stl_keys = item.Keys()
	returnList = []
	copyKeys = stl_keys.__class__(stl_keys) #wlav suggested workaround. Make a copy first
	for x in copyKeys:
		k = x.c_str()
		returnList.append(k)
	return returnList

def processItem(item):
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
