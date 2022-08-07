import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	face = item[0]
	area = 0.0
	if isinstance(face, topologic.Face):
		area = topologic.FaceUtility.Area(face)
	return area

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
	
class SvFaceArea(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the area of the input Face    
	"""
	bl_idname = 'SvFaceArea'
	bl_label = 'Face.Area'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Area')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Area'].sv_set([0.0])
			return
		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		outputs = recur(faceList)
		self.outputs['Area'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceArea)

def unregister():
	bpy.utils.unregister_class(SvFaceArea)
