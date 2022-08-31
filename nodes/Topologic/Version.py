import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import re

class SvTopologicVersion(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the current version of Topologic    
	"""
	bl_idname = 'SvTopologicVersion'
	bl_label = 'Topologic.Version'

	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Version')

	def process(self):
		self.outputs['Version'].sv_set(['0 8 2 4'])


def register():
	bpy.utils.register_class(SvTopologicVersion)

def unregister():
	bpy.utils.unregister_class(SvTopologicVersion)
