import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	topologyEdges = []
	edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	_ = item.Edges(edges)
	for anEdge in edges:
		topologyEdges.append(anEdge)
	return topologyEdges

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
		
class SvTopologyEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Edges of the input Topology    
	"""
	bl_idname = 'SvTopologyEdges'
	bl_label = 'Topology.Edges'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Edges')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Edges'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		if len(outputs) == 1:
			outputs = outputs[0]
		self.outputs['Edges'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyEdges)

def unregister():
	bpy.utils.unregister_class(SvTopologyEdges)
