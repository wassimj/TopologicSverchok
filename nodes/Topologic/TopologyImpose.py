import bpy
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

class SvTopologyImpose(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology representing the Boolean Impose of the tool Topology on the input Topology
	"""
	bl_idname = 'SvTopologyImpose'
	bl_label = 'Topology.Impose'
	TransferDictionary: BoolProperty(name="Transfer Dictionary", default=False, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology A')
		self.inputs.new('SvStringsSocket', 'Impose')
		self.inputs.new('SvStringsSocket', 'Transfer Dictionary').prop_name = 'TransferDictionary'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyAList = self.inputs['Topology A'].sv_get(deepcopy=True)[0]
		topologyBList = self.inputs['Impose'].sv_get(deepcopy=True)[0]
		trasnferDictionary = self.inputs['Transfer Dictionary'].sv_get(deepcopy=False)[0][0]
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
				try:
					resultList.append(topologic.Topology.Impose(aTopologyPair[0], aTopologyPair[1]))
				except:
					print("Error: Impose Operation Failed!")
					continue
			self.outputs['Topology'].sv_set([resultList])


def register():
    bpy.utils.register_class(SvTopologyImpose)

def unregister():
    bpy.utils.unregister_class(SvTopologyImpose)
