import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	contexts = []
	_ = item.Contexts(contexts)
	return contexts

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

class SvTopologyContexts(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Contexts of the input Topology    
	"""
	bl_idname = 'SvTopologyContexts'
	bl_label = 'Topology.Contexts'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Contexts')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Contexts'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = recur(inputs)
		if(len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['Contexts'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyContexts)

def unregister():
	bpy.utils.unregister_class(SvTopologyContexts)
