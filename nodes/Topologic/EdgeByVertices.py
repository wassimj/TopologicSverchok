import bpy
from bpy.props import StringProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(vertices):
	print(vertices)
	if len(vertices) < 2:
		return None
	stl_vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	for v in vertices:
		stl_vertices.push_back(v)
	edge = topologic.EdgeUtility.ByVertices(stl_vertices)
	print(edge)
	return edge

class SvEdgeByVertices(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates an Edge from the input Vertices
	"""
	bl_idname = 'SvEdgeByVertices'
	bl_label = 'Edge.ByVertices'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertices')
		self.outputs.new('SvStringsSocket', 'Edge')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Edge'].sv_set([])
			return
		vList = self.inputs['Vertices'].sv_get(deepcopy=False)
		if isinstance(vList[0], list) == False:
			vList = [vList]
		outputs = []
		for anInput in vList:
			outputs.append(processItem(anInput))
		self.outputs['Edge'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvEdgeByVertices)

def unregister():
    bpy.utils.unregister_class(SvEdgeByVertices)
