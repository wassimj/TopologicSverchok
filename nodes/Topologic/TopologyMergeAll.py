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
	resultTopology = item[0]
	topologies = []
	for i in range(1, len(item)):
		resultTopology = resultTopology.Union(item[i])
	cells = []
	_ = resultTopology.Cells(None, cells)
	unused = []
	for i in range(len(item)):
		unused.append(True)
	sets = []
	for i in range(len(cells)):
		sets.append([])
	for i in range(len(item)):
		if unused[i]:
			iv = topologic.CellUtility.InternalVertex(item[i], 0.0001)
			for j in range(len(cells)):
				if (topologic.CellUtility.Contains(cells[j], iv, 0.0001) == 0):
					sets[j].append(item[i])
					unused[i] = False
	return sets

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

class SvTopologyMergeAll(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Merges all the input Topologies into one Topology
	"""
	bl_idname = 'SvTopologyMergeAll'
	bl_label = 'Topology.MergeAll'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topologies')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topologies'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		topology = processItem(inputs)
		self.outputs['Topology'].sv_set([topology])
		end = time.time()
		print("Topology.MergeAll Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyMergeAll)

def unregister():
    bpy.utils.unregister_class(SvTopologyMergeAll)
