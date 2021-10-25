import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary

def processItem(item):
	return topologic.Topology.ByOcctShape(item, "")

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem(input)
	return output
		
class SvTopologyByOCCTShape(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Topology of the input OCCT shape (TopoDS_Shape)   
	"""
	bl_idname = 'SvTopologyByOCCTShape'
	bl_label = 'Topology.ByOCCTShape'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'OCCT Shape')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyByOCCTShape)

def unregister():
	bpy.utils.unregister_class(SvTopologyByOCCTShape)
