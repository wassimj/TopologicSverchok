import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def unitizeVector(vector):
	mag = 0
	for value in vector:
		mag += value ** 2
	mag = mag ** 0.5
	unitVector = []
	for i in range(len(vector)):
		unitVector.append(vector[i] / mag)
	return unitVector

def processItem(item):
	edge, mantissa = item
	assert isinstance(edge, topologic.Edge), "Edge.Direction - Error: Input is not an Edge"
	ev = edge.EndVertex()
	sv = edge.StartVertex()
	x = ev.X() - sv.X()
	y = ev.Y() - sv.Y()
	z = ev.Z() - sv.Z()
	uvec = unitizeVector([x,y,z])
	x = round(uvec[0], mantissa)
	y = round(uvec[1], mantissa)
	z = round(uvec[2], mantissa)
	return [x, y, z]

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

class SvEdgeDirection(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the direction vector of the input Edge    
	"""
	bl_idname = 'SvEdgeDirection'
	bl_label = 'Edge.Direction'
	bl_icon = 'SELECT_DIFFERENCE'

	Direction:StringProperty(name="Direction", update=updateNode)
	Mantissa: IntProperty(name="Mantissa", default=4, min=0, max=8, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.outputs.new('SvStringsSocket', 'Direction').prop_name="Direction"
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
		self.outputs['Direction'].sv_set(output)

def register():
	bpy.utils.register_class(SvEdgeDirection)

def unregister():
	bpy.utils.unregister_class(SvEdgeDirection)
