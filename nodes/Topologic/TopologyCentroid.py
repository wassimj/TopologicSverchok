import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	vert = None
	try:
		vert = item.Centroid()
	except:
		vert = None
	return vert

class SvTopologyCentroid(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the centroid of the input Topologic
	"""
	bl_idname = 'SvTopologyCentroid'
	bl_label = 'Topology Centroid'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Centroid')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Centroid'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyCentroid)

def unregister():
	bpy.utils.unregister_class(SvTopologyCentroid)
