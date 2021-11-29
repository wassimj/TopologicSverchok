import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
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

def processItem(item):
	bfv1 = topologic.FaceUtility.VertexAtParameters(item,0,0)
	bfv2 = topologic.FaceUtility.VertexAtParameters(item,1,0)
	bfv3 = topologic.FaceUtility.VertexAtParameters(item,1,1)
	bfv4 = topologic.FaceUtility.VertexAtParameters(item,0,1)
	bfe1 = topologic.Edge.ByStartVertexEndVertex(bfv1,bfv2)
	bfe2 = topologic.Edge.ByStartVertexEndVertex(bfv2,bfv3)
	bfe3 = topologic.Edge.ByStartVertexEndVertex(bfv3,bfv4)
	bfe4 = topologic.Edge.ByStartVertexEndVertex(bfv4,bfv1)
	bfw1 = topologic.Wire.ByEdges([bfe1,bfe2,bfe3,bfe4])
	return topologic.Face.ByExternalBoundary(bfw1)

class SvFaceBoundingFace(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Bounding Face of the input Face    
	"""
	bl_idname = 'SvFaceBoundingFace'
	bl_label = 'Face.BoundingFace'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Face'].sv_set([])
			return
		inputs = self.inputs['Face'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceBoundingFace)

def unregister():
	bpy.utils.unregister_class(SvFaceBoundingFace)
