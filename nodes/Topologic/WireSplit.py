import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import EdgeIsCollinear

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def edgeOtherVertex(edge, vertex):
	vertices = []
	_ = edge.Vertices(None, vertices)
	if topologic.Topology.IsSame(vertex, vertices[0]):
		return vertices[-1]
	else:
		return vertices[0]

def vertexOtherEdge(vertex, edge, wire):
	edges = []
	_ = vertex.Edges(wire, edges)
	if topologic.Topology.IsSame(edges[0], edge):
		return edges[-1]
	else:
		return edges[0]

def vertexDegree(v, wire):
	edges = []
	_ = v.Edges(wire, edges)
	return len(edges)

def edgeInList(edge, edgeList):
	for anEdge in edgeList:
		if topologic.Topology.IsSame(anEdge, edge):
			return True
	return False

def processItem(wire):
	vertices = []
	_ = wire.Vertices(None, vertices)
	hubs = []
	for aVertex in vertices:
		if vertexDegree(aVertex, wire) > 2:
			hubs.append(aVertex)
	wires = []
	global_edges = []
	for aVertex in hubs:
		hub_edges = []
		_ = aVertex.Edges(wire, hub_edges)
		wire_edges = []
		for hub_edge in hub_edges:
			if not edgeInList(hub_edge, global_edges):
				current_edge = hub_edge
				oe = edgeOtherVertex(current_edge, aVertex)
				while vertexDegree(oe, wire) == 2:
					if not edgeInList(current_edge, global_edges):
						global_edges.append(current_edge)
						wire_edges.append(current_edge)
					current_edge = vertexOtherEdge(oe, current_edge, wire)
					oe = edgeOtherVertex(current_edge, oe)
				if not edgeInList(current_edge, global_edges):
					global_edges.append(current_edge)
					wire_edges.append(current_edge)
				if len(wire_edges) > 1:
					wires.append(topologic.Cluster.ByTopologies(wire_edges).SelfMerge())
				else:
					wires.append(wire_edges[0])
				wire_edges = []
	if len(wires) < 1:
		return wire
	return wires

class SvWireSplit(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Split the input Wire into one or more manifold wires.
	"""
	bl_idname = 'SvWireSplit'
	bl_label = 'Wire.Split'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.outputs.new('SvStringsSocket', 'Wires')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		wires = self.inputs['Wire'].sv_get(deepcopy=False)

		wires = flatten(wires)
		output = []
		for aWire in wires:
			output.append(processItem(aWire))
		self.outputs['Wires'].sv_set(output)

def register():
    bpy.utils.register_class(SvWireSplit)

def unregister():
    bpy.utils.unregister_class(SvWireSplit)
