import bpy
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

class SvCellComplexByFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a CellComplex from the list of input Faces  
	"""
	bl_idname = 'SvCellComplexByFaces'
	bl_label = 'CellComplex.ByFaces'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Faces')
		self.outputs.new('SvStringsSocket', 'CellComplex')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Faces'].sv_get(deepcopy=False)
		cellcomplexes = []
		for faceList in inputs:
			faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
			for face in faceList:
				faces.push_back(face)
			cellcomplexes.append(topologic.CellComplex.ByFaces(faces))
		self.outputs['CellComplex'].sv_set([cellcomplexes])

def register():
    bpy.utils.register_class(SvCellComplexByFaces)

def unregister():
    bpy.utils.unregister_class(SvCellComplexByFaces)
