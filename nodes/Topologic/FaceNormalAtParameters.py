import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
def matchLengths(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

def processItem(item, outputType, decimals):
	coords = None
	face = item[0]
	u = item[1]
	v = item[2]
	try:
		coords = topologic.FaceUtility.NormalAtParameters(face, u, v)
		x = round(coords.X(), decimals)
		y = round(coords.Y(), decimals)
		z = round(coords.Z(), decimals)
		returnResult = []
		if outputType == "XYZ":
			returnResult = [x,y,z]
		elif outputType == "XY":
			returnResult = [x,y]
		elif outputType == "XZ":
			returnResult = [x,z]
		elif outputType == "YZ":
			returnResult = [y,z]
		elif outputType == "X":
			returnResult = x
		elif outputType == "Y":
			returnResult = y
		elif outputType == "Z":
			returnResult = z
	except:
		returnResult = None
	return returnResult

outputTypes = [("XYZ", "XYZ", "", 1),("XY", "XY", "", 2),("XZ", "XZ", "", 3),("YZ", "YZ", "", 4),("X", "X", "", 5), ("Y", "Y", "", 6),("Z", "Z", "", 7)]

class SvFaceNormalAtParameters(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the normal of the input Face at the input UV parameters    
	"""
	bl_idname = 'SvFaceNormalAtParameters'
	bl_label = 'Face.NormalAtParameters'
	Coordinates:StringProperty(name="Normal", update=updateNode)
	Decimals: IntProperty(name="Decimals", default=4, min=0, max=8, update=updateNode)
	outputType: EnumProperty(name="Output Type", description="Specify output type", default="XYZ", items=outputTypes, update=updateNode)
	U: FloatProperty(name="U", default=0.5, precision=4, update=updateNode)
	V: FloatProperty(name="Y",  default=0.5, precision=4, update=updateNode)


	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'U').prop_name = 'U'
		self.inputs.new('SvStringsSocket', 'V').prop_name = 'V'
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
		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		uList = self.inputs['U'].sv_get(deepcopy=False)[0]
		vList = self.inputs['V'].sv_get(deepcopy=False)[0]
		decimals = self.inputs['Decimals'].sv_get(deepcopy=False)[0][0] #Consider only one Decimals value

		matchLengths([faceList, uList, vList])
		inputs = zip(faceList, uList, vList)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, self.outputType, decimals))
		self.outputs['Coordinates'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceNormalAtParameters)

def unregister():
	bpy.utils.unregister_class(SvFaceNormalAtParameters)
