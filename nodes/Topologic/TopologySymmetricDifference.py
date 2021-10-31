import bpy
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import time

def processItem(item):
	topologyA = item[0]
	topologyB = item[1]
	tranDict = item[2]
	topologyC = None
	try:
		topologyC = topologyA.XOR(topologyB, tranDict)
	except:
		print("ERROR: (Topologic>Topology.SymmetricDifference) operation failed.")
		topologyC = None
	return topologyC

class SvTopologySymmetricDifference(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology representing the Boolean Symmetric Difference of the two input Topologies
	"""
	bl_idname = 'SvTopologySymmetricDifference'
	bl_label = 'Topology.SymmetricDifference'
	TransferDictionary: BoolProperty(name="Transfer Dictionary", default=False, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology A')
		self.inputs.new('SvStringsSocket', 'Topology B')
		self.inputs.new('SvStringsSocket', 'Transfer Dictionary').prop_name = 'TransferDictionary'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		topologyAList = self.inputs['Topology A'].sv_get(deepcopy=False)
		topologyBList = self.inputs['Topology B'].sv_get(deepcopy=False)
		tranDictList = self.inputs['Transfer Dictionary'].sv_get(deepcopy=False)[0]
		maxLength = max([len(topologyAList), len(topologyBList), len(tranDictList)])
		for i in range(len(topologyAList), maxLength):
			topologyAList.append(topologyAList[-1])
		for i in range(len(topologyBList), maxLength):
			topologyBList.append(topologyBList[-1])
		for i in range(len(tranDictList), maxLength):
			tranDictList.append(tranDictList[-1])
		inputs = []
		outputs = []
		if (len(topologyAList) == len(topologyBList) == len(tranDictList)):
			inputs = zip(topologyAList, topologyBList, tranDictList)
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)
		end = time.time()
		print("Symmetric Difference Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologySymmetricDifference)

def unregister():
    bpy.utils.unregister_class(SvTopologySymmetricDifference)
