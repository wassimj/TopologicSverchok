import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def unitizeVector(vector):
	mag = 0
	for value in vector:
		mag += value ** 2
	mag = mag ** 0.5
	unitVector = []
	for i in range(len(vector)):
		unitVector.append(vector[i] / mag)
	return unitVector

def processItem(item, outputType, decimals):
	coords = None
	print(item)
	ev = item.EndVertex()
	sv = item.StartVertex()
	x = ev.X() - sv.X()
	y = ev.Y() - sv.Y()
	z = ev.Z() - sv.Z()
	uvec = unitizeVector([x,y,z])
	x = round(uvec[0], decimals)
	y = round(uvec[1], decimals)
	z = round(uvec[2], decimals)
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
	return [coords, x, y, z]

outputTypes = [("XYZ", "XYZ", "", 1),("XY", "XY", "", 2),("XZ", "XZ", "", 3),("YZ", "YZ", "", 4),("X", "X", "", 5), ("Y", "Y", "", 6),("Z", "Z", "", 7)]

class SvEdgeDirection(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the direction vector of the input Edge    
	"""
	bl_idname = 'SvEdgeDirection'
	bl_label = 'Edge.Direction'
	Direction:StringProperty(name="Direction", update=updateNode)
	Decimals: IntProperty(name="Decimals", default=4, min=0, max=8, update=updateNode)
	outputType: EnumProperty(name="Output Type", description="Specify output type", default="XYZ", items=outputTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.inputs.new('SvStringsSocket', 'Decimals').prop_name = 'Decimals'
		self.outputs.new('SvStringsSocket', 'Direction').prop_name="Direction"
		self.outputs.new('SvStringsSocket', 'X')
		self.outputs.new('SvStringsSocket', 'Y')
		self.outputs.new('SvStringsSocket', 'Z')

	def draw_buttons(self, context, layout):
		layout.prop(self, "outputType",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Direction'].sv_set([])
			return
		edgeList = self.inputs['Edge'].sv_get(deepcopy=False)
		edgeList = flatten(edgeList)
		decimals = self.inputs['Decimals'].sv_get(deepcopy=False)[0][0] #Consider only one Decimals value
		directionList = []
		xList = []
		yList = []
		zList = []
		for anEdge in edgeList:
			output = processItem(anEdge, self.outputType, decimals)
			directionList.append(output[0])
			xList.append(output[1])
			yList.append(output[2])
			zList.append(output[3])
		self.outputs['Direction'].sv_set(directionList)
		self.outputs['X'].sv_set(xList)
		self.outputs['Y'].sv_set(yList)
		self.outputs['Z'].sv_set(zList)

def register():
	bpy.utils.register_class(SvEdgeDirection)

def unregister():
	bpy.utils.unregister_class(SvEdgeDirection)
