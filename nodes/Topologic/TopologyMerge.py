import bpy
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

class SvTopologyMerge(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology representing the Boolean Merge of the two input Topologies
	"""
	bl_idname = 'SvTopologyMerge'
	bl_label = 'Topology.Merge'
	TransferDictionary: BoolProperty(name="Transfer Dictionary", default=False, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology A')
		self.inputs.new('SvStringsSocket', 'Topology B')
		self.inputs.new('SvStringsSocket', 'Transfer Dictionary').prop_name = 'TransferDictionary'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not (self.inputs['Topology A'].is_linked):
			return
		if not (self.inputs['Topology B'].is_linked):
			return
		topologyA = self.inputs['Topology A'].sv_get(deepcopy=False)[0][0]
		topologyB = self.inputs['Topology B'].sv_get(deepcopy=False)[0][0]
		transferDictionary = self.inputs['Transfer Dictionary'].sv_get(deepcopy=False)[0][0]
		print(topologyA)
		print(topologyB)
		resultTopology = topologyA.Merge(topologyB, transferDictionary)
		self.outputs['Topology'].sv_set([resultTopology])

'''
		maxLength = max([len(topologyAList), len(topologyBList)])
		for i in range(len(topologyAList), maxLength):
			topologyAList.append(topologyAList[-1])
		for i in range(len(topologyBList), maxLength):
			topologyBList.append(topologyBList[-1])
		topologies = []
		if (len(topologyAList) == len(topologyBList)):
			topologies = zip(topologyAList, topologyBList)
			resultList = []
			for aTopologyPair in topologies:
				print(aTopologyPair[0])
				print(aTopologyPair[1])
				#dcopy = topologic.Topology.DeepCopy(aTopologyPair[0])
				#print(dcopy)
				if aTopologyPair[0] != None and aTopologyPair[1] != None:
					print("Attempting Merge operation...")
					resultTopology = aTopologyPair[0].Merge(aTopologyPair[1], transferDictionary)
					resultList.append(resultTopology)
			self.outputs['Topology'].sv_set([resultList])
'''

def register():
    bpy.utils.register_class(SvTopologyMerge)

def unregister():
    bpy.utils.unregister_class(SvTopologyMerge)
