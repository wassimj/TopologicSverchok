import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

#from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
from topologic import Dictionary

def processItem(item):
	if isinstance(item, dict):
		return list(item.keys())
	elif isinstance(item, Dictionary):
		return item.Keys()
	else:
		return None

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
	
class SvDictionaryKeys(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the list of values of the input Dictionary   
	"""
	bl_idname = 'SvDictionaryKeys'
	bl_label = 'Dictionary.Keys'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Dictionary')
		self.outputs.new('SvStringsSocket', 'Keys')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		
		inputs = self.inputs['Dictionary'].sv_get(deepcopy=True)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		if len(outputs) == 1:
			outputs = outputs[0]
		self.outputs['Keys'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDictionaryKeys)

def unregister():
	bpy.utils.unregister_class(SvDictionaryKeys)
