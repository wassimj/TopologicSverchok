import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
import cppyy
from cppyy.gbl.std import string, list
		
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
		
		DictionaryList = self.inputs['Dictionary'].sv_get(deepcopy=True)
		output = []
		for i in range(len(DictionaryList)):
			values = DictionaryList[i][0].Values()
			py_values = []
			for aValue in values:
				s = cppyy.bind_object(aValue.Value(), 'StringStruct')
				py_values.append(str(s.getString))
			output.append(py_values)
		self.outputs['Values'].sv_set(output)

def register():
	bpy.utils.register_class(SvDictionaryValues)

def unregister():
	bpy.utils.unregister_class(SvDictionaryValues)
