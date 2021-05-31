import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import cppyy

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


def processItem(item):
	apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
	_ = item.Apertures(apertures)
	return list(apertures)

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output = recur(anItem)
	else:
		output = processItem(input)
	return output
		
class SvTopologyApertures(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Apertures of the input Topology    
	"""
	bl_idname = 'SvTopologyApertures'
	bl_label = 'Topology.Apertures'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Apertures')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Apertures'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Apertures'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyApertures)

def unregister():
	bpy.utils.unregister_class(SvTopologyApertures)
