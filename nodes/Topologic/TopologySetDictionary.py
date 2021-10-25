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

class SvTopologySetDictionary(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Sets the input Dictionary to the input Topology   
	"""
	bl_idname = 'SvTopologySetDictionary'
	bl_label = 'Topology.SetDictionary'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Dictionary')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		TopologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		DictionaryList = self.inputs['Dictionary'].sv_get(deepcopy=False)
		TopologyList = flatten(TopologyList)
		DictionaryList = flatten(DictionaryList)
		if len(TopologyList) != len(DictionaryList):
			return
		for i in range(len(TopologyList)):
			_ = TopologyList[i].SetDictionary(DictionaryList[i])
		self.outputs['Topology'].sv_set(TopologyList)

def register():
	bpy.utils.register_class(SvTopologySetDictionary)

def unregister():
	bpy.utils.unregister_class(SvTopologySetDictionary)
