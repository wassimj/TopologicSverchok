import bpy
from bpy.props import IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvCellComplexType(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the type number of the CellComplex class
	"""
	bl_idname = 'SvCellComplexType'
	bl_label = 'CellComplex.Type'
	Type: IntProperty(name="Type", default=0, update=updateNode)
	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Type').prop_name = 'Type'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		self.outputs['Type'].sv_set([topologic.CellComplex.Type()])

def register():
	bpy.utils.register_class(SvCellComplexType)

def unregister():
	bpy.utils.unregister_class(SvCellComplexType)
