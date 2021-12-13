import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
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
	return topologic.Cluster.ByTopologies(item)

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

class SvClusterByTopologies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cluster from the list of input Topologies  
	"""
	bl_idname = 'SvClusterByTopologies'
	bl_label = 'Cluster.ByTopologies'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topologies')
		self.outputs.new('SvStringsSocket', 'Cluster')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topologies'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Cluster'].sv_set(outputs)
		end = time.time()
		print("Cluster.ByTopologies Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvClusterByTopologies)

def unregister():
    bpy.utils.unregister_class(SvClusterByTopologies)
