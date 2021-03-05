import bpy
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

class SvFaceByEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face from the list of input Edges    
	"""
	bl_idname = 'SvFaceByEdges'
	bl_label = 'Face.ByEdges'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Edges'].sv_get(deepcopy=False)
		edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		faces = []
		for edgeList in inputs:
			for edge in edgeList:
				edges.push_back(edge)
		faces.append(topologic.Face.ByEdges(edges))
		self.outputs['Face'].sv_set([wires])

def register():
    bpy.utils.register_class(SvFaceByEdges)

def unregister():
    bpy.utils.unregister_class(SvFaceByEdges)
