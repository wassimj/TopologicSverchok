import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import math

def processItem(item):
	face, mantissa = item
	exb = face.ExternalBoundary()
	edges = []
	_ = exb.Edges(None, edges)
	perimeter = 0.0
	for anEdge in edges:
		perimeter = perimeter + abs(topologic.EdgeUtility.Length(anEdge))
	area = abs(topologic.FaceUtility.Area(face))
	compactness  = 0
	#From https://en.wikipedia.org/wiki/Compactness_measure_of_a_shape

	if area <= 0:
		raise Exception("Error: Face.Compactness: Face area is less than or equal to zero")
	if perimeter <= 0:
		raise Exception("Error: Face.Compactness: Face perimeter is less than or equal to zero")
	compactness = (math.pi*(2*math.sqrt(area/math.pi)))/perimeter
	return round(compactness, mantissa)

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

class SvFaceCompactness(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the compactness (isoperimetric quotient) measure of the input Face    
	"""
	bl_idname = 'SvFaceCompactness'
	bl_label = 'Face.Compactness'
	bl_icon = 'SELECT_DIFFERENCE'

	Mantissa: IntProperty(name="Mantissa", default=4, min=0, max=8, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Compactness')
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
		self.outputs['Compactness'].sv_set(output)

def register():
	bpy.utils.register_class(SvFaceCompactness)

def unregister():
	bpy.utils.unregister_class(SvFaceCompactness)
