import bpy
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

class SvWireByEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Wire from the list of input Edges    
	"""
	bl_idname = 'SvWireByEdges'
	bl_label = 'Wire.ByEdges'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Wire')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Edges'].sv_get(deepcopy=False)
		edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		wires = []
		for edgeList in inputs:
			for edge in edgeList:
				edges.push_back(edge)
		wires.append(topologic.Wire.ByEdges(edges))
		self.outputs['Wire'].sv_set([wires])

def register():
    bpy.utils.register_class(SvWireByEdges)

def unregister():
    bpy.utils.unregister_class(SvWireByEdges)
