import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

#from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
from topologic import Dictionary

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	return item.GetDictionary()

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

class SvTopologyDictionary(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Dictionary of the input Topology   
	"""
	bl_idname = 'SvTopologyDictionary'
	bl_label = 'Topology.Dictionary'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Dictionary')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Dictionary'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyDictionary)

def unregister():
	bpy.utils.unregister_class(SvTopologyDictionary)
