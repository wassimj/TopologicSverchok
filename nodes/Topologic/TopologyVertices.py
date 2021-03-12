import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	topologyVertices = []
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	_ = item.Vertices(vertices)
	for aVertex in vertices:
		topologyVertices.append(aVertex)
	return topologyVertices

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

class SvTopologyVertices(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Vertices of the input Topology    
	"""
	bl_idname = 'SvTopologyVertices'
	bl_label = 'Topology.Vertices'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Vertices')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Vertices'].sv_set([])
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		outputs = recur(inputs)
		if (len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['Vertices'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyVertices)

def unregister():
	bpy.utils.unregister_class(SvTopologyVertices)
