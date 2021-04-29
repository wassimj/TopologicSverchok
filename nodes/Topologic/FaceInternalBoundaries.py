import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	wires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	_ = item.InternalBoundaries(wires)
	return list(wires)

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

class SvFaceInternalBoundaries(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the internal boundaries (Wires) of the input Face    
	"""
	bl_idname = 'SvFaceInternalBoundaries'
	bl_label = 'Face.InternalBoundaries'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Wires')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Cell'].sv_set([])
			return
		inputs = self.inputs['Cell'].sv_get(deepcopy=False)
		outputs = recur(inputs)
		if (len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['Wires'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceInternalBoundaries)

def unregister():
	bpy.utils.unregister_class(SvFaceInternalBoundaries)
