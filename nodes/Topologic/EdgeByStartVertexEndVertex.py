import bpy
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

class SvEdgeByStartVertexEndVertex(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates an Edge from the input Vertices
	"""
	bl_idname = 'SvEdgeByStartVertexEndVertex'
	bl_label = 'Edge.ByStartVertexEndVertex'
	startVertex: StringProperty(name="StartVertex", update=updateNode)
	endVertex: StringProperty(name="EndVertex", update=updateNode)

	def sv_init(self, context):
		#self.inputs.new('SvStringsSocket', 'StartVertex').prop_name = 'StartVertex'
		#self.inputs.new('SvStringsSocket', 'EndVertex').prop_name = 'EndVertex'
		self.inputs.new('SvStringsSocket', 'StartVertex')
		self.inputs.new('SvStringsSocket', 'EndVertex')
		self.outputs.new('SvStringsSocket', 'Edge')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		startVertices = self.inputs['StartVertex'].sv_get(deepcopy=False)[0]
		endVertices = self.inputs['EndVertex'].sv_get(deepcopy=False)[0]
		maxLength = max([len(startVertices), len(endVertices)])
		for i in range(len(startVertices), maxLength):
			startVertices.append(startVertices[-1])
		for i in range(len(endVertices), maxLength):
			endVertices.append(endVertices[-1])
		vertices = []
		if (len(startVertices) == len(endVertices)):
			vertices = zip(startVertices, endVertices)
			edges = []
			for aVertexPair in vertices:
				try:
					edges.append(topologic.Edge.ByStartVertexEndVertex(aVertexPair[0], aVertexPair[1]))
				except:
					continue
			self.outputs['Edge'].sv_set([edges])


def register():
    bpy.utils.register_class(SvEdgeByStartVertexEndVertex)

def unregister():
    bpy.utils.unregister_class(SvEdgeByStartVertexEndVertex)
