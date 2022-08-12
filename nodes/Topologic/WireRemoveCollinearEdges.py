import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import EdgeIsCollinear, WireSplit, WireByVertices

def edgeOtherEnd(edge, vertex):
	vertices = []
	_ = edge.Vertices(None, vertices)
	if topologic.Topology.IsSame(vertex, vertices[0]):
		return vertices[-1]
	else:
		return vertices[0]

def vertexDegree(v, wire):
	edges = []
	_ = v.Edges(wire, edges)
	return len(edges)

def removeCollinearEdges(wire, angTol):
	final_Wire = None
	vertices = []
	wire_verts = []
	_ = wire.Vertices(None, vertices)
	for aVertex in vertices:
		edges = []
		_ = aVertex.Edges(wire, edges)
		if len(edges) > 1:
			if not EdgeIsCollinear.processItem([edges[0], edges[1], angTol]):
				wire_verts.append(aVertex)
		else:
			wire_verts.append(aVertex)
	if len(wire_verts) > 2:
		clus = topologic.Cluster.ByTopologies(wire_verts)
		if wire.IsClosed():
			final_wire = WireByVertices.processItem([clus, True])
		else:
			final_wire = WireByVertices.processItem([clus, False])
	elif len(wire_verts) == 2:
		final_wire = topologic.Edge.ByStartVertexEndVertex(wire_verts[0], wire_verts[1])
	return final_wire

def processItem(item):
	wire, angTol = item
	if not topologic.Topology.IsManifold(wire, wire):
		wires = WireSplit.processItem(wire)
	else:
		wires = [wire]
	returnWires = []
	for aWire in wires:
		returnWires.append(removeCollinearEdges(aWire, angTol))
	if len(returnWires) == 1:
		return returnWires[0]
	elif len(returnWires) > 1:
		return topologic.Cluster.ByTopologies(returnWires).SelfMerge()
	else:
		return None

def recur(input, angTol):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem, angTol))
	else:
		output = processItem([input, angTol])
	return output

class SvWireRemoveCollinearEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Removes any collinear edges from the input Wire    
	"""
	bl_idname = 'SvWireRemoveCollinearEdges'
	bl_label = 'Wire.RemoveCollinearEdges'
	bl_icon = 'SELECT_DIFFERENCE'

	AngTol: FloatProperty(name='Angular Tolerance', default=0.1, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.outputs.new('SvStringsSocket', 'Wire')
		self.width = 225
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"
	
	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Angular Tolerance")
		split.row().prop(self, "AngTol",text="")

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		input = self.inputs[0].sv_get(deepcopy=False)
		output = recur(input, self.AngTol)
		if not isinstance(output, list):
			output = [output]
		self.outputs['Wire'].sv_set(output)

def register():
    bpy.utils.register_class(SvWireRemoveCollinearEdges)

def unregister():
    bpy.utils.unregister_class(SvWireRemoveCollinearEdges)
