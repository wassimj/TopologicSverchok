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
		topologicCore = 'TopologicCore: '+str(topologic.TopologicCore.About.Version())
		filename = (topologic.__file__)
		result = re.search('topologic-(.*)-py', filename)
		topologicPy = 'TopologicPy: '+result.group(1)
		topologicSverchok = 'TopologicSverchok: 0.5.4.6'
		versions = [topologicCore, topologicPy, topologicSverchok]
		self.outputs['Version'].sv_set(versions)


def register():
	bpy.utils.register_class(SvTopologicVersion)

def unregister():
	bpy.utils.unregister_class(SvTopologicVersion)
