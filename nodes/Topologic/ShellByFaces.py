import bpy
from bpy.props import StringProperty
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

def processItem(faces):
	stl_faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	for face in faces:
		stl_faces.push_back(face)
	return topologic.Shell.ByFaces(stl_faces)

class SvShellByFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Shell from the list of input Faces  
	"""
	bl_idname = 'SvShellByFaces'
	bl_label = 'Shell.ByFaces'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Faces')
		self.outputs.new('SvStringsSocket', 'Shell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		faceList = self.inputs['Faces'].sv_get(deepcopy=False)
		if isinstance(faceList[0], list) == False:
			faceList = [faceList]
		output = []
		for faces in faceList:
			output.append(processItem(faces))
		self.outputs['Shell'].sv_set(output)

def register():
    bpy.utils.register_class(SvShellByFaces)

def unregister():
    bpy.utils.unregister_class(SvShellByFaces)
