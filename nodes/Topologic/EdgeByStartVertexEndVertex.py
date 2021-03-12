import bpy
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	sv = item[0]
	ev = item[1]
	edge = None
	try:
		edge = topologic.Edge.ByStartVertexEndVertex(sv, ev)
	except:
		edge = None
	return edge

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
		self.inputs.new('SvStringsSocket', 'StartVertex')
		self.inputs.new('SvStringsSocket', 'EndVertex')
		self.outputs.new('SvStringsSocket', 'Edge')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Edge'].sv_set([])
			return
		startVertices = self.inputs['StartVertex'].sv_get(deepcopy=False)
		endVertices = self.inputs['EndVertex'].sv_get(deepcopy=False)
		maxLength = max([len(startVertices), len(endVertices)])
		for i in range(len(startVertices), maxLength):
			startVertices.append(startVertices[-1])
		for i in range(len(endVertices), maxLength):
			endVertices.append(endVertices[-1])
		outputs = []
		inputs = []
		if (len(startVertices) == len(endVertices)):
			inputs = zip(startVertices, endVertices)
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Edge'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvEdgeByStartVertexEndVertex)

def unregister():
    bpy.utils.unregister_class(SvEdgeByStartVertexEndVertex)
