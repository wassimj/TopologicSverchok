import bpy
from bpy.props import IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvClusterType(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the type number of the Cluster class
	"""
	bl_idname = 'SvClusterType'
	bl_label = 'Cluster.Type'
	Type: IntProperty(name="Type", default=0, update=updateNode)
	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Type').prop_name = 'Type'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		self.outputs['Type'].sv_set([topologic.Cluster.Type()])

def register():
	bpy.utils.register_class(SvClusterType)

def unregister():
	bpy.utils.unregister_class(SvClusterType)
