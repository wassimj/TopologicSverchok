import bpy
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import time

def processItem(item):
	vertices = []
	_ = item.Vertices(vertices)
	edges = []
	_ = item.Edges(vertices, 0.001, edges)
	return edges

class SvGraphEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Edges of the input Graph
	"""
	bl_idname = 'SvGraphEdges'
	bl_label = 'Graph.Edges'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.outputs.new('SvStringsSocket', 'Edges')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Edges'].sv_set([])
			return
		inputs = self.inputs['Graph'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Edges'].sv_set(outputs)
		end = time.time()
		print("Graph.Edges Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphEdges)

def unregister():
    bpy.utils.unregister_class(SvGraphEdges)
