import bpy
from bpy.props import IntProperty, EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic
from . import Replication

def processItem(item):
	return topologic.Aperture.Topology(item)

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem(input)
	return output

class SvApertureTopology(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Topology of the input Aperture   
	"""
	bl_idname = 'SvApertureTopology'
	bl_label = 'Aperture.Topology'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Aperture')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		apertureList = self.inputs['Aperture'].sv_get(deepcopy=True)
		self.outputs['Topology'].sv_set(recur(apertureList))

def register():
    bpy.utils.register_class(SvApertureTopology)

def unregister():
    bpy.utils.unregister_class(SvApertureTopology)
