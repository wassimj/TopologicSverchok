import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from mathutils import Matrix

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item, outputType, decimals):
	if item:
		coords = None
		x = round(item.X(), decimals)
		y = round(item.Y(), decimals)
		z = round(item.Z(), decimals)
		coords = (x,y,z)
		matrix = Matrix([[1,0,0,x],
				[0,1,0,y],
				[0,0,1,z],
				[0,0,0,1]])
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
		return [coords, matrix, x, y, z]
	else:
		return [None,Matrix(),None, None, None]

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
		self.outputs.new('SvVerticesSocket', 'Coordinates')
		self.outputs.new('SvMatrixSocket', 'Matrix')
		self.outputs.new('SvStringsSocket', 'X')
		self.outputs.new('SvStringsSocket', 'Y')
		self.outputs.new('SvStringsSocket', 'Z')

	def draw_buttons(self, context, layout):
		layout.prop(self, "outputType",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Coordinates'].sv_set([])
			return
		vertexList = self.inputs['Vertex'].sv_get(deepcopy=False)
		vertexList = flatten(vertexList)
		decimals = self.inputs['Decimals'].sv_get(deepcopy=False)[0][0] #Consider only one Decimals value
		coordinatesList = []
		matrixList = []
		xList = []
		yList = []
		zList = []
		for aVertex in vertexList:
			output = processItem(aVertex, self.outputType, decimals)
			coordinatesList.append(output[0])
			matrixList.append(output[1])
			xList.append(output[2])
			yList.append(output[3])
			zList.append(output[4])
		self.outputs['Coordinates'].sv_set(coordinatesList)
		self.outputs['Matrix'].sv_set(matrixList)
		self.outputs['X'].sv_set(xList)
		self.outputs['Y'].sv_set(yList)
		self.outputs['Z'].sv_set(zList)

def register():
	bpy.utils.register_class(SvVertexCoordinates)

def unregister():
	bpy.utils.unregister_class(SvVertexCoordinates)
