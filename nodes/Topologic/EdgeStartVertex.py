import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	edge = item[0]
	vert = None
	try:
		vert = edge.StartVertex()
	except:
		vert = None
	return vert

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem([input])
	return output

class SvEdgeStartVertex(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the start Vertex of the input Edge
	"""
	bl_idname = 'SvEdgeStartVertex'
	bl_label = 'Edge.StartVertex'
	bl_icon = 'SELECT_DIFFERENCE'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.outputs.new('SvStringsSocket', 'StartVertex')
		self.width = 150
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		input = self.inputs[0].sv_get(deepcopy=False)
		output = recur(input)
		if not isinstance(output, list):
			output = [output]
		self.outputs['StartVertex'].sv_set(output)

def register():
	bpy.utils.register_class(SvEdgeStartVertex)

def unregister():
	bpy.utils.unregister_class(SvEdgeStartVertex)
