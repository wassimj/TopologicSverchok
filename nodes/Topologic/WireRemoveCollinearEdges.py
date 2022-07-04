import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import EdgeIsCollinear, WireSplit, WireByVertices

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

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
		if wire.IsClosed():
			final_wire = WireByVertices.processItem([wire_verts, True])
		else:
			final_wire = WireByVertices.processItem([wire_verts, False])
	elif len(wire_verts) == 2:
		final_wire = topologic.Edge.ByStartVertexEndVertex(wire_verts[0], wire_verts[1])
	return final_wire

def processItem(item, angTol):
	if not topologic.Topology.IsManifold(item, item):
		wires = WireSplit.processItem(item)
	else:
		wires = [item]
	returnWires = []
	for aWire in wires:
		returnWires.append(removeCollinearEdges(aWire, angTol))
	return topologic.Cluster.ByTopologies(returnWires).SelfMerge()

class SvWireRemoveCollinearEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Removes any collinear edges from the input Wire    
	"""
	bl_idname = 'SvWireRemoveCollinearEdges'
	bl_label = 'Wire.RemoveCollinearEdges'
	AngTol: FloatProperty(name='Angular Tolerance', default=0.1, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.inputs.new('SvStringsSocket', 'Angular Tolerance').prop_name='AngTol'
		self.outputs.new('SvStringsSocket', 'Wire')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		wires = self.inputs['Wire'].sv_get(deepcopy=False)
		angTol = self.inputs['Angular Tolerance'].sv_get(deepcopy=False)[0]

		wires = flatten(wires)
		output = []
		for aWire in wires:
			output.append(processItem(aWire, angTol))
		self.outputs['Wire'].sv_set(output)

def register():
    bpy.utils.register_class(SvWireRemoveCollinearEdges)

def unregister():
    bpy.utils.unregister_class(SvWireRemoveCollinearEdges)
