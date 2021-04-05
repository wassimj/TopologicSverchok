import bpy
from bpy.props import IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvShellType(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the type number of the Shell class
	"""
	bl_idname = 'SvShellType'
	bl_label = 'Shell.Type'
	Type: IntProperty(name="Type", default=0, update=updateNode)
	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Type').prop_name = 'Type'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		self.outputs['Type'].sv_set([topologic.Shell.Type()])

def register():
	bpy.utils.register_class(SvShellType)

def unregister():
	bpy.utils.unregister_class(SvShellType)
