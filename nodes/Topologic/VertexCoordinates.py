import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item, outputType, decimals):
	coords = None
	try:
		x = round(item.X(), decimals)
		y = round(item.Y(), decimals)
		z = round(item.Z(), decimals)
		coords = [x,y,z]
		if outputType == "XYZ":
			coords = [x,y,z]
		elif outputType == "XY":
			coords = [x,y]
		elif outputType == "XZ":
			coords = [x,z]
		elif outputType == "YZ":
			coords = [y,z]
		elif outputType == "X":
			coords = x
		elif outputType == "Y":
			coords = y
		elif outputType == "Z":
			coords = z
	except:
		coords = None
	return coords

def recur(input, outputType, decimals):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem, outputType, decimals))
	else:
		output = processItem(input, outputType, decimals)
	return output

outputTypes = [("XYZ", "XYZ", "", 1),("XY", "XY", "", 2),("XZ", "XZ", "", 3),("YZ", "YZ", "", 4),("X", "X", "", 5), ("Y", "Y", "", 6),("Z", "Z", "", 7)]

class SvVertexCoordinates(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the coordinates of the input Vertex    
	"""
	bl_idname = 'SvVertexCoordinates'
	bl_label = 'Vertex.Coordinates'
	Coordinates:StringProperty(name="Coordinates", update=updateNode)
	Decimals: IntProperty(name="Decimals", default=4, min=0, max=8, update=updateNode)
	outputType: EnumProperty(name="Output Type", description="Specify output type", default="XYZ", items=outputTypes, update=updateNode)


	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.inputs.new('SvStringsSocket', 'Decimals').prop_name = 'Decimals'
		self.outputs.new('SvStringsSocket', 'Coordinates').prop_name="Coordinates"

	def draw_buttons(self, context, layout):
		layout.prop(self, "outputType",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Coordinates'].sv_set([])
			return
		inputs = self.inputs['Vertex'].sv_get(deepcopy=False)
		decimals = self.inputs['Decimals'].sv_get(deepcopy=False)[0][0] #Consider only one Decimals value

		outputs = recur(inputs, self.outputType, decimals)	
		self.outputs['Coordinates'].sv_set(outputs)


def register():
	bpy.utils.register_class(SvVertexCoordinates)

def unregister():
	bpy.utils.unregister_class(SvVertexCoordinates)
