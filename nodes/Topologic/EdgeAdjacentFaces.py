import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	edges = []
	_ = item.AdjacentFaces(edges)
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

class SvEdgeAdjacentFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Faces connected to the input Edge
	"""
	bl_idname = 'SvEdgeAdjacentFaces'
	bl_label = 'Edge.AdjacentFaces'
	Face: StringProperty(name="Face", update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.outputs.new('SvStringsSocket', 'Faces').prop_name = 'Face'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Edge'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Faces'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEdgeAdjacentFaces)

def unregister():
	bpy.utils.unregister_class(SvEdgeAdjacentFaces)
