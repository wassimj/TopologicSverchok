import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	topologyWires = []
	wires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	_ = item.Wires(wires)
	for aWire in wires:
		topologyWires.append(aWire)
	return topologyWires

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
		
class SvTopologyWires(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Wires of the input Topology    
	"""
	bl_idname = 'SvTopologyWires'
	bl_label = 'Topology.Wires'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Wires')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Wires'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = recur(inputs)
		if (len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['Wires'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyWires)

def unregister():
	bpy.utils.unregister_class(SvTopologyWires)
