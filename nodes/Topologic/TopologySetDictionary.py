import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
import cppyy
from cppyy.gbl.std import string, list
		
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
		if len(TopologyList) != len(DictionaryList):
			return
		for i in range(len(TopologyList)):
			_ = TopologyList[i][0].SetDictionary(DictionaryList[i][0])
		self.outputs['Topology'].sv_set(TopologyList)

def register():
	bpy.utils.register_class(SvTopologySetDictionary)

def unregister():
	bpy.utils.unregister_class(SvTopologySetDictionary)
