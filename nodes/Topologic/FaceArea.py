import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	if item:
		return topologic.FaceUtility.Area(item)
	else:
		return None
		
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
			self.outputs['Face'].sv_set([])
			return
		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		faceList = flatten(faceList)
		outputs = []
		for face in faceList:
			outputs.append(processItem(face))
		self.outputs['Area'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceArea)

def unregister():
	bpy.utils.unregister_class(SvFaceArea)
