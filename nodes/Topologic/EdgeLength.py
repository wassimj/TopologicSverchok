import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	edge, mantissa = item
	length = None
	try:
		length = round(topologic.EdgeUtility.Length(edge), mantissa)
	except:
		length = None
	return length

def recur(input, mantissa):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem, mantissa))
	else:
		output = processItem([input, mantissa])
	return output

class SvEdgeLength(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the length of the input Edge    
	"""
	bl_idname = 'SvEdgeLength'
	bl_label = 'Edge.Length'
	bl_icon = 'SELECT_DIFFERENCE'

	Mantissa: IntProperty(name="Mantissa", default=4, min=0, max=8, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.outputs.new('SvStringsSocket', 'Length')
		self.width = 150
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"
	
	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Mantissa")
		split.row().prop(self, "Mantissa",text="")

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		input = self.inputs[0].sv_get(deepcopy=False)
		output = recur(input, self.Mantissa)
		if not isinstance(output, list):
			output = [output]
		self.outputs['Length'].sv_set(output)

def register():
	bpy.utils.register_class(SvEdgeLength)

def unregister():
	bpy.utils.unregister_class(SvEdgeLength)
