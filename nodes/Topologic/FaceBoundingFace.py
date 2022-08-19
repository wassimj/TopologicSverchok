import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	face = item[0]
	bfv1 = topologic.FaceUtility.VertexAtParameters(face,0,0)
	bfv2 = topologic.FaceUtility.VertexAtParameters(face,1,0)
	bfv3 = topologic.FaceUtility.VertexAtParameters(face,1,1)
	bfv4 = topologic.FaceUtility.VertexAtParameters(face,0,1)
	bfe1 = topologic.Edge.ByStartVertexEndVertex(bfv1,bfv2)
	bfe2 = topologic.Edge.ByStartVertexEndVertex(bfv2,bfv3)
	bfe3 = topologic.Edge.ByStartVertexEndVertex(bfv3,bfv4)
	bfe4 = topologic.Edge.ByStartVertexEndVertex(bfv4,bfv1)
	bfw1 = topologic.Wire.ByEdges([bfe1,bfe2,bfe3,bfe4])
	return topologic.Face.ByExternalBoundary(bfw1)

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem([input])
	return output

class SvFaceBoundingFace(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the axis-aligned bounding Face of the input Face    
	"""
	bl_idname = 'SvFaceBoundingFace'
	bl_label = 'Face.BoundingFace'
	bl_icon = 'SELECT_DIFFERENCE'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Face')
		self.width = 175
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
		self.outputs['Face'].sv_set(output)

def register():
	bpy.utils.register_class(SvFaceBoundingFace)

def unregister():
	bpy.utils.unregister_class(SvFaceBoundingFace)
