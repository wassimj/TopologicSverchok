import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time
import pyvisgraph as vg

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(cluster):
	wires = []
	_ = cluster.Wires(None, wires)
	polys = []
	for aWire in wires:
		vertices = []
		_ = aWire.Vertices(None, vertices)
		poly = []
		for v in vertices:
			p = vg.Point(round(v.X(),4),round(v.Y(),4), 0)
			poly.append(p)
		polys.append(poly)
	g = vg.VisGraph()
	g.build(polys)
	tpEdges = []
	vgEdges = g.visgraph.get_edges()
	for vgEdge in vgEdges:
		sv = topologic.Vertex.ByCoordinates(vgEdge.p1.x, vgEdge.p1.y,0)
		ev = topologic.Vertex.ByCoordinates(vgEdge.p2.x, vgEdge.p2.y,0)
		tpEdges.append(topologic.Edge.ByStartVertexEndVertex(sv, ev))
	tpVertices = []
	vgPoints = g.visgraph.get_points()
	for vgPoint in vgPoints:
		v = topologic.Vertex.ByCoordinates(vgPoint.x, vgPoint.y,0)
		tpVertices.append(v)
	graph = topologic.Graph(tpVertices, tpEdges)
	return graph

class SvGraphVisibilityGraph(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a 2D Visibility Graph of the input Cluster of Wires
	"""
	bl_idname = 'SvGraphVisibilityGraph'
	bl_label = 'Graph.VisibilityGraph'
	
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Obstacles Cluster')
		self.outputs.new('SvStringsSocket', 'Graph')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Graph'].sv_set([])
			return
		clusters = self.inputs['Obstacles Cluster'].sv_get(deepcopy=True)
		clusters = flatten(clusters)
		outputs = []
		for aCluster in clusters:
			outputs.append(processItem(aCluster))
		self.outputs['Graph'].sv_set(outputs)
		end = time.time()
		print("Graph.ByTopology Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphVisibilityGraph)

def unregister():
    bpy.utils.unregister_class(SvGraphVisibilityGraph)
