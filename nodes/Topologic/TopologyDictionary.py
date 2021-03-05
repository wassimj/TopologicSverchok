import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
import cppyy
from cppyy.gbl.std import string, list
		
class SvTopologyDictionary(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Sets the input Dictionary to the input Topology   
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
		TopologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		output = []
		for i in range(len(TopologyList)):
			output.append([TopologyList[i][0].GetDictionary()])
		self.outputs['Dictionary'].sv_set(output)

def register():
	bpy.utils.register_class(SvTopologyDictionary)

def unregister():
	bpy.utils.unregister_class(SvTopologyDictionary)
