import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from mathutils import Matrix

def processItem(item):
	vertex, outputType, mantissa = item
	if vertex:
		output = None
		x = round(vertex.X(), mantissa)
		y = round(vertex.Y(), mantissa)
		z = round(vertex.Z(), mantissa)
		matrix = Matrix([[1,0,0,x],
				[0,1,0,y],
				[0,0,1,z],
				[0,0,0,1]])
		if outputType == "XYZ":
			output = [x,y,z]
		elif outputType == "XY":
			output = [x,y]
		elif outputType == "XZ":
			output = [x,z]
		elif outputType == "YZ":
			output = [y,z]
		elif outputType == "X":
			output = x
		elif outputType == "Y":
			output = y
		elif outputType == "Z":
			output = z
		elif outputType == "Matrix":
			output = matrix
		return output
	else:
		if outputType == "Matrix":
			return Matrix()
		else:
			return None

def recur(input, outputType, mantissa):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem, outputType, mantissa))
	else:
		output = processItem([input, outputType, mantissa])
	return output

outputTypes = [("XYZ", "XYZ", "", 1),("XY", "XY", "", 2),("XZ", "XZ", "", 3),("YZ", "YZ", "", 4),("X", "X", "", 5), ("Y", "Y", "", 6),("Z", "Z", "", 7)]

class SvVertexCoordinates(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the coordinates of the input Vertex    
	"""
	bl_idname = 'SvVertexCoordinates'
	bl_label = 'Vertex.Coordinates'
	bl_icon = 'SELECT_DIFFERENCE'

	Coordinates:StringProperty(name="Coordinates", update=updateNode)
	Mantissa: IntProperty(name="Mantissa", default=4, min=0, max=8, update=updateNode)
	OutputType: EnumProperty(name="Output", description="Specify output type", default="XYZ", items=outputTypes, update=updateNode)
	id_matrix = (1.0, 0.0, 0.0, 0.0,
                 0.0, 1.0, 0.0, 0.0,
                 0.0, 0.0, 1.0, 0.0,
                 0.0, 0.0, 0.0, 1.0)
	matrix: FloatVectorProperty(
        name="matrix", description="matrix", default=id_matrix,
        subtype='MATRIX', size=16, precision=3, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.outputs.new('SvVerticesSocket', 'Coordinates')
		self.outputs.new('SvMatrixSocket', "Matrix").prop_name='matrix'
		self.width = 175
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.2)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Output")
		split.row().prop(self, "OutputType",text="")
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Mantissa")
		split.row().prop(self, "Mantissa",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Coordinates'].sv_set([])
			return
		vertexList = self.inputs['Vertex'].sv_get(deepcopy=False)
		self.outputs['Coordinates'].sv_set(recur(vertexList, self.OutputType, self.Mantissa))
		self.outputs['Matrix'].sv_set(recur(vertexList, "Matrix", self.Mantissa))

def register():
	bpy.utils.register_class(SvVertexCoordinates)

def unregister():
	bpy.utils.unregister_class(SvVertexCoordinates)
