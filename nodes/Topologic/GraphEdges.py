import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import time


def processItem(graph, tolerance):
	vertices = []
	_ = graph.Vertices(vertices)
	edges = []
	_ = graph.Edges(vertices, tolerance, edges)
	return edges

class SvGraphEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Edges of the input Graph
	"""
	bl_idname = 'SvGraphEdges'
	bl_label = 'Graph.Edges'
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Edges')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Edges'].sv_set([])
			return
		inputs = self.inputs['Graph'].sv_get(deepcopy=False)
		tolerance = self.inputs['Tolerance'].sv_get(deepcopy=True)[0][0]
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, tolerance))
		self.outputs['Edges'].sv_set(outputs)
		end = time.time()
		print("Graph.Edges Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphEdges)

def unregister():
    bpy.utils.unregister_class(SvGraphEdges)
