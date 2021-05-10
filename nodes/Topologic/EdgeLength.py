import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	return topologic.EdgeUtility.Length(item)
		
class SvEdgeLength(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the length of the input Edge    
	"""
	bl_idname = 'SvEdgeLength'
	bl_label = 'Edge.Length'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.outputs.new('SvStringsSocket', 'Length')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Edge'].sv_set([])
			return
		faceList = self.inputs['Edge'].sv_get(deepcopy=False)
		faceList = flatten(faceList)
		outputs = []
		for face in faceList:
			outputs.append(processItem(face))
		self.outputs['Length'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEdgeLength)

def unregister():
	bpy.utils.unregister_class(SvEdgeLength)
