import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

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
	return topologic.Topology.IsSame(item[0], item[1])

def matchLengths(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

class SvTopologyIsSame(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the two input Topologies are the same. Outpute False otherwise.   
	"""
	bl_idname = 'SvTopologyIsSame'
	bl_label = 'Topology.IsSame'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology A')
		self.inputs.new('SvStringsSocket', 'Topology B')
		self.outputs.new('SvStringsSocket', 'Is Same')

	def process(self):
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Is Same'].sv_set([False])
			return
		topologyAList = self.inputs['Topology A'].sv_get(deepcopy=False)
		topologyBList = self.inputs['Topology B'].sv_get(deepcopy=False)
		topologyAList = flatten(topologyAList)
		topologyBList = flatten(topologyBList)
		matchLengths([topologyAList, topologyBList])
		inputs = zip(topologyAList, topologyBList)
		output = []
		for anInput in inputs:
			output.append(processItem(anInput))
		self.outputs['Is Same'].sv_set(output)

def register():
	bpy.utils.register_class(SvTopologyIsSame)

def unregister():
	bpy.utils.unregister_class(SvTopologyIsSame)
