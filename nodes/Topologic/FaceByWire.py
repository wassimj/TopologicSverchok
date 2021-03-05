import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	internalBoundaries = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	face = topologic.Face.ByExternalInternalBoundaries(item, internalBoundaries)
	return face

def recur(input, output):
	print(input)
	if isinstance(input, list):
		newList = []
		for anItem in input:
			returnValue = recur(anItem, output)
			newList.append(returnValue)
		output.append(newList)
	else:
		returnValue = processItem(input)
		output.append(returnValue)
	return output
		
class SvFaceByWire(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face from the input planar closed Wire   
	"""
	bl_idname = 'SvFaceByWire'
	bl_label = 'Face.ByWire'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs = recur(anInput, outputs)
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceByWire)

def unregister():
	bpy.utils.unregister_class(SvFaceByWire)
