import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import time

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	graph = item
	vertices = []
	_ = graph.IsolatedVertices(vertices)
	return vertices

class SvGraphIsolatedVertices(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Vertices that are isolated (not connected to any edges) within the input Graph
	"""
	bl_idname = 'SvGraphIsolatedVertices'
	bl_label = 'Graph.IsolatedVertices'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.outputs.new('SvStringsSocket', 'Vertices')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Graph'].sv_get(deepcopy=True)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Vertices'].sv_set(outputs)
		end = time.time()
		print("Graph Isolated Vertices Operation consumed "+str(round(end - start,4))+" seconds")
def register():
    bpy.utils.register_class(SvGraphIsolatedVertices)

def unregister():
    bpy.utils.unregister_class(SvGraphIsolatedVertices)
