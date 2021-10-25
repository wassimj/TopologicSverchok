import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	edges = []
	_ = item.AdjacentWires(edges)
	return edges

def recur(item):
	output = []
	if item == None:
		return []
	if isinstance(item, list):
		for anItem in item:
			output.append(recur(anItem))
	else:
		output = processItem(item)
	return output

class SvEdgeAdjacentWires(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Wires connected to the input Edge
	"""
	bl_idname = 'SvEdgeAdjacentWires'
	bl_label = 'Edge.AdjacentWires'
	Wire: StringProperty(name="Wire", update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.outputs.new('SvStringsSocket', 'Wires').prop_name = 'Wire'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Edge'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Wires'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEdgeAdjacentWires)

def unregister():
	bpy.utils.unregister_class(SvEdgeAdjacentWires)
