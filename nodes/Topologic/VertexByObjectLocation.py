import bpy
from sverchok.node_tree import SverchCustomTreeNode

import topologic
from . import Replication

def processItem(item):
	# hack to get an updated item from the scene. Might not be needed.
	if item:
		item = bpy.data.objects[item.name]
		vector = item.matrix_world.translation
		vert = None
		try:
			vert = topologic.Vertex.ByCoordinates(vector[0], vector[1], vector[2])
		except:
			vert = None
		return vert
	else:
		return None

def recur(item):
	output = []
	if item == None:
		return []
	if isinstance(item, list):
		for subItem in item:
			output.append(recur(subItem))
	else:
		output = processItem(item)
	return output

class SvVertexByObjectLocation(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Vertex from the location of the input Blender object  
	"""
	bl_idname = 'SvVertexByObjectLocation'
	bl_label = 'Vertex.ByObjectLocation'
	bl_icon = 'SELECT_DIFFERENCE'

	def sv_init(self, context):
		self.width = 200
		self.inputs.new('SvStringsSocket', 'Object')
		self.outputs.new('SvStringsSocket', 'Vertex')
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.2)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		objList = self.inputs['Object'].sv_get(deepcopy=True)
		self.outputs['Vertex'].sv_set(recur(objList))

def register():
    bpy.utils.register_class(SvVertexByObjectLocation)

def unregister():
    bpy.utils.unregister_class(SvVertexByObjectLocation)
