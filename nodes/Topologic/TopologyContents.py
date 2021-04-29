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
	topologyContents = []
	contents = cppyy.gbl.std.list[topologic.Topology.Ptr]()
	_ = item.Contents(contents)
	for aContent in contents:
		aContent.__class__ = classByType(aContent.GetType())
		topologyContents.append(aContent)
	return topologyContents

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
		
class SvTopologyContents(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the content Topologies of the input Topology    
	"""
	bl_idname = 'SvTopologyContents'
	bl_label = 'Topology.Contents'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Contents')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Contents'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Contents'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyContents)

def unregister():
	bpy.utils.unregister_class(SvTopologyContents)
