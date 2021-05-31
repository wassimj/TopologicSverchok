import bpy
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import cppyy
import time


def classByType(argument):
	switcher = {
		1: Vertex,
		2: Edge,
		4: Wire,
		8: Face,
		16: Shell,
		32: Cell,
		64: CellComplex,
		128: Cluster }
	return switcher.get(argument, Topology)

def fixTopologyClass(topology):
  topology.__class__ = classByType(topology.GetType())
  return topology

def processItem(item):
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	try:
		_ = item.Vertices(vertices)
	except:
		print("ERROR: (Topologic>Graph.Vertices) operation failed.")
		vertices = None
	return list(vertices)

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
