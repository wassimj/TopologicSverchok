import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
from . import Replication

def processItem(item):
	assert isinstance(item, list), "face.ByEdges - Error: Input is not a list"
	edges = [x for x in item if isinstance(x, topologic.Edge)]
	wire = None
	face = None
	for anEdge in edges:
		if anEdge.Type() == 2:
			if wire == None:
				wire = anEdge
			else:
				try:
					wire = wire.Merge(anEdge)
				except:
					continue
	if wire.Type() != 4:
		return None
	else:
		try:
			face = topologic.Face.ByExternalBoundary(wire)
		except:
			return None
	return face

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

class SvFaceByEdges(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face from the list of input Edges    
	"""
	bl_idname = 'SvFaceByEdges'
	bl_label = 'Face.ByEdges'
	bl_icon = 'SELECT_DIFFERENCE'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Face')
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
		self.outputs['Face'].sv_set(output)

def register():
    bpy.utils.register_class(SvFaceByEdges)

def unregister():
    bpy.utils.unregister_class(SvFaceByEdges)
