import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	return topologic.Topology.Analyze(item)

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output = recur(anItem)
	else:
		output = processItem(input)
	return output
		
class SvTopologyAnalyze(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the analysis of the input Topology    
	"""
	bl_idname = 'SvTopologyAnalyze'
	bl_label = 'Topology.Analyze'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Analysis')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Analysis'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Analysis'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyAnalyze)

def unregister():
	bpy.utils.unregister_class(SvTopologyAnalyze)
