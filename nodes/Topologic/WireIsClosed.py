import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
class SvWireIsClosed(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the input Wire is closed. Outputs False otherwise   
	"""
	bl_idname = 'SvWireIsClosed'
	bl_label = 'Wire.IsClosed'
	Wire: StringProperty(name="Wire", update=updateNode)
	Bool: BoolProperty(name="Bool", default=False, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.outputs.new('SvStringsSocket', 'Bool').prop_name = 'Bool'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)[0]
		outputs = []
		for anInput in inputs:
			outputs.append(anInput.IsClosed())
		self.outputs['Bool'].sv_set([outputs])

def register():
	bpy.utils.register_class(SvWireIsClosed)

def unregister():
	bpy.utils.unregister_class(SvWireIsClosed)
