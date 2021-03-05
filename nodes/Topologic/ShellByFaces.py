import bpy
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

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
		inputs = self.inputs['Faces'].sv_get(deepcopy=False)
		shells = []
		for faceList in inputs:
			faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
			for face in faceList:
				faces.push_back(face)
			shells.append(topologic.Shell.ByFaces(faces))
		self.outputs['Shell'].sv_set([shells])

def register():
    bpy.utils.register_class(SvShellByFaces)

def unregister():
    bpy.utils.unregister_class(SvShellByFaces)
