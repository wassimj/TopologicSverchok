import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	topologyShells = []
	shells = cppyy.gbl.std.list[topologic.Shell.Ptr]()
	_ = item.Shells(shells)
	for aShell in shells:
		topologyShells.append(aShell)
	return topologyShells

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
		
class SvTopologyShells(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Shells of the input Topology    
	"""
	bl_idname = 'SvTopologyShells'
	bl_label = 'Topology.Shells'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Shells')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Shells'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			print(anInput)
			outputs.append(recur(anInput))
		self.outputs['Shells'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyShells)

def unregister():
	bpy.utils.unregister_class(SvTopologyShells)
