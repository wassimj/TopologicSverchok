import bpy
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import time

def processItem(graph):
	vertices = []
	if graph:
		try:
			_ = graph.Vertices(vertices)
		except:
			print("ERROR: (Topologic>Graph.Vertices) operation failed.")
			vertices = None
	if vertices:
		return vertices
	else:
		return []

class SvGraphVertices(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Vertices of the input Graph
	"""
	bl_idname = 'SvGraphVertices'
	bl_label = 'Graph.Vertices'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.outputs.new('SvStringsSocket', 'Vertices')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Vertices'].sv_set([])
			return
		inputs = self.inputs['Graph'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Vertices'].sv_set(outputs)
		end = time.time()
		print("Graph.Vertices Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphVertices)

def unregister():
    bpy.utils.unregister_class(SvGraphVertices)
