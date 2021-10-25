import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
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
	return topologic.Topology.DeepCopy(item)

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input[0], list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem(input)
	return output

class SvTopologyCopy(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology that represents a copy of the input Topology  
	"""
	bl_idname = 'SvTopologyCopy'
	bl_label = 'Topology.Copy'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)
		end = time.time()
		print("Topology.Copy Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyCopy)

def unregister():
    bpy.utils.unregister_class(SvTopologyCopy)
