import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	assert isinstance(item, list), "Edge.ByVertices - Error: Input is not a list"
	vertices = [x for x in item if isinstance(x, topologic.Vertex)]
	if len(vertices) < 2:
		return None
	elif len(vertices) == 2:
		return topologic.Edge.ByStartVertexEndVertex(vertices[0], vertices[-1])
	else:
		edges = []
		for i in range(len(vertices)-1):
			edges.append(topologic.Edge.ByStartVertexEndVertex(vertices[i], vertices[i+1]))
		return edges

def recur(item):
	output = []
	if item == None:
		return []
	if isinstance(item[0], list):
		for subItem in item:
			output.append(recur(subItem))
	else:
		output = processItem(item)
	return output

class SvEdgeByVertices(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates an Edge from the input Vertices
	"""
	bl_idname = 'SvEdgeByVertices'
	bl_label = 'Edge.ByVertices'
	bl_icon = 'SELECT_DIFFERENCE'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertices')
		self.outputs.new('SvStringsSocket', 'Edge')
		self.width = 150
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		input = self.inputs[0].sv_get(deepcopy=False)
		output = recur(input)
		if not isinstance(output, list):
			output = [output]
		self.outputs['Edge'].sv_set(output)

def register():
    bpy.utils.register_class(SvEdgeByVertices)

def unregister():
    bpy.utils.unregister_class(SvEdgeByVertices)
