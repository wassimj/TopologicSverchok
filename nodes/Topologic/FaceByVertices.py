import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
from . import Replication, TopologySelfMerge

def processItem(item):
	assert isinstance(item, list), "Face.ByVertices - Error: Input is not a list"
	vertices = [x for x in item if isinstance(x, topologic.Vertex)]
	edges = []
	for i in range(len(vertices)-1):
		v1 = vertices[i]
		v2 = vertices[i+1]
		try:
			e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
			if e:
				edges.append(e)
		except:
			continue
	v1 = vertices[-1]
	v2 = vertices[0]
	try:
		e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
		if e:
			edges.append(e)
	except:
		pass
	if len(edges) > 0:
		return topologic.Face.ByExternalBoundary(TopologySelfMerge.processItem(topologic.Cluster.ByTopologies(edges, False)))
	else:
		return None

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

class SvFaceByVertices(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face from the list of input Vertices. The Vertices are assumed to be ordered. The last Vertex will be automatically connected to the first Vertex to close the loop.    
	"""
	bl_idname = 'SvFaceByVertices'
	bl_label = 'Face.ByVertices'
	bl_icon = 'SELECT_DIFFERENCE'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertices')
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
    bpy.utils.register_class(SvFaceByVertices)

def unregister():
    bpy.utils.unregister_class(SvFaceByVertices)
