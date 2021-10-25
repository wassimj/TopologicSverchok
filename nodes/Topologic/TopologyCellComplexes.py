import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	topologyCellComplexes = []
	ptr = topologic.CellComplex.Ptr
	cellcomplexes = cppyy.gbl.std.list[ptr]()
	_ = item.CellComplexes(cellcomplexes)
	for aCellComplex in cellcomplexes:
		topologyCellComplexes.append(aCellComplex)
	return topologyCellComplexes

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
		
class SvTopologyCellComplexes(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the CellComplexes of the input Topology    
	"""
	bl_idname = 'SvTopologyCellComplexes'
	bl_label = 'Topology.CellComplexes'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'CellComplexes')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['CellComplexes'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = recur(input)
		if (len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['CellComplexes'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyCellComplexes)

def unregister():
	bpy.utils.unregister_class(SvTopologyCellComplexes)
