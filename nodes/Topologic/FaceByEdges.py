import bpy
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	return topologic.Face.ByEdges(item)

class SvFaceByEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face from the list of input Edges    
	"""
	bl_idname = 'SvFaceByEdges'
	bl_label = 'Face.ByEdges'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Edges'].sv_get(deepcopy=True)
		if isinstance(inputs[0], list) == False:
			inputs = [inputs]
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Face'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvFaceByEdges)

def unregister():
    bpy.utils.unregister_class(SvFaceByEdges)
