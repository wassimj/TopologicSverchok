import bpy
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import time

def processItem(item):
	return item.Topology()

class SvGraphTopology(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Topology of the input Graph
	"""
	bl_idname = 'SvGraphTopology'
	bl_label = 'Graph.Topology'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		inputs = self.inputs['Graph'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)
		end = time.time()
		print("Graph.Topology Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphTopology)

def unregister():
    bpy.utils.unregister_class(SvGraphTopology)
