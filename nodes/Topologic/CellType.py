import bpy
from bpy.props import IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvCellType(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Outputs the type number of the Cell class
	"""
	bl_idname = 'SvCellType'
	bl_label = 'Cell.Type'
	Type: IntProperty(name="Type", default=0, update=updateNode)
	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Type').prop_name = 'Type'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		self.outputs['Type'].sv_set([topologic.Cell.Type()])

def register():
	bpy.utils.register_class(SvCellType)

def unregister():
	bpy.utils.unregister_class(SvCellType)
