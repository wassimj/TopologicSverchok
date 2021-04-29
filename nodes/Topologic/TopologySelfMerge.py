import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	topology = item.SelfMerge()
	return topology

class SvTopologySelfMerge(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Self-merges the input Topology
	"""
	bl_idname = 'SvTopologySelfMerge'
	bl_label = 'Topology.SelfMerge'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologySelfMerge)

def unregister():
	bpy.utils.unregister_class(SvTopologySelfMerge)
