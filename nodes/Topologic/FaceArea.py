import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	face, mantissa = item
	area = None
	try:
		area = round(topologic.FaceUtility.Area(face), mantissa)
	except:
		area = None
	return area

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
	
class SvFaceArea(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Outputs the area of the input Face    
	"""
	bl_idname = 'SvFaceArea'
	bl_label = 'Face.Area'
	bl_icon = 'SELECT_DIFFERENCE'

	Mantissa: IntProperty(name="Mantissa", default=4, min=0, max=8, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Area')
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
		self.outputs['Area'].sv_set(output)

def register():
	bpy.utils.register_class(SvFaceArea)

def unregister():
	bpy.utils.unregister_class(SvFaceArea)
