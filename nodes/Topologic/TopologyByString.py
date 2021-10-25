import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

def processItem(item):
	return topologic.Topology.DeepCopy(Topology.ByString(item))
		
class SvTopologyByString(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology from the input BREP string
	"""
	bl_idname = 'SvTopologyByString'
	bl_label = 'Topology.ByString'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'String')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		inputs = self.inputs['String'].sv_get(deepcopy=False)
		if isinstance(inputs[0], list):
			newInputs = []
			for anInput in inputs:
				newInputs.append(anInput[0])
		else:
			newInputs = inputs
		outputs = []
		for anInput in newInputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyByString)

def unregister():
	bpy.utils.unregister_class(SvTopologyByString)
