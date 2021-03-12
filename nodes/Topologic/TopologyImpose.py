import bpy
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
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
	topologyA = item[0]
	topologyB = item[1]
	tranDict = item[2]
	topologyC = None
	try:
		topologyC = fixTopologyClass(topologyA.Impose(topologyB, tranDict))
	except:
		print("ERROR: (Topologic>Topology.Impose) operation failed.")
		topologyC = None
	return topologyC

class SvTopologyImpose(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology representing the Boolean Impose of the tool on the input Topology
	"""
	bl_idname = 'SvTopologyImpose'
	bl_label = 'Topology.Impose'
	TransferDictionary: BoolProperty(name="Transfer Dictionary", default=False, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Tool')
		self.inputs.new('SvStringsSocket', 'Transfer Dictionary').prop_name = 'TransferDictionary'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		topologyAList = self.inputs['Topology'].sv_get(deepcopy=False)
		topologyBList = self.inputs['Tool'].sv_get(deepcopy=False)
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
		print("Impose Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyImpose)

def unregister():
    bpy.utils.unregister_class(SvTopologyImpose)
