import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvEdgeStartVertex(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the start Vertex of the input Edge
	"""
	bl_idname = 'SvEdgeStartVertex'
	bl_label = 'Edge Start Vertex'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.outputs.new('SvStringsSocket', 'StartVertex').prop_name = 'StartVertex'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)[0]
		outputs = []
		for anInput in inputs:
			try:
				outputs.append(anInput.StartVertex())
			except:
				continue
	
		self.outputs['StartVertex'].sv_set([outputs])

def register():
	bpy.utils.register_class(SvEdgeStartVertex)

def unregister():
	bpy.utils.unregister_class(SvEdgeStartVertex)
