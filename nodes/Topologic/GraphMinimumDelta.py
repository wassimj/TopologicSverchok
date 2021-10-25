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
	return item.MinimumDelta()

class SvGraphMinimumDelta(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the minimum delta of the input Graph
	"""
	bl_idname = 'SvGraphMinimumDelta'
	bl_label = 'Graph.MinimumDelta'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.outputs.new('SvStringsSocket', 'Min Delta')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		inputs = self.inputs['Graph'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Min Delta'].sv_set(outputs)
		end = time.time()
		print("Graph Minimum Delta Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphMinimumDelta)

def unregister():
    bpy.utils.unregister_class(SvGraphMinimumDelta)
