import bpy
from bpy.props import StringProperty, BoolProperty
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
	return item.IsComplete()

class SvGraphIsComplete(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the input Graph is complete (all vertices are connected to each other). Outputs False otherwise.
	"""
	bl_idname = 'SvGraphIsComplete'
	bl_label = 'Graph.IsComplete'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.outputs.new('SvStringsSocket', 'Boolean')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		inputs = self.inputs['Graph'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Boolean'].sv_set(outputs)
		end = time.time()
		print("Graph IsComplete Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphIsComplete)

def unregister():
    bpy.utils.unregister_class(SvGraphIsComplete)
