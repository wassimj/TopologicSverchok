import bpy
from bpy.props import FloatProperty, StringProperty
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

def processItem(face):
	faceTriangles = cppyy.gbl.std.list[topologic.Face.Ptr]()
	for i in range(0,5,1):
		try:
			_ = topologic.FaceUtility.Triangulate(face, float(i)*0.1, faceTriangles)
			return list(faceTriangles)
		except:
			continue
	return [face]

class SvFaceTriangulate(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a list of Faces that represent the triangulation of the input Face
	"""
	bl_idname = 'SvFaceTriangulate'
	bl_label = 'Face.Triangulate'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Faces')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		faces = self.inputs['Face'].sv_get(deepcopy=False)
		faces = flatten(faces)
		outputs = []
		for aFace in faces:
			outputs.append(processItem(aFace))
		self.outputs['Faces'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceTriangulate)

def unregister():
	bpy.utils.unregister_class(SvFaceTriangulate)
