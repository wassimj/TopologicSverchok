import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	faces = []
	_ = item.InternalBoundaries(faces)
	return faces

class SvCellComplexInternalBoundaries(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the internal boundaries (Faces) of the input CellComplex    
	"""
	bl_idname = 'SvCellComplexInternalBoundaries'
	bl_label = 'CellComplex.InternalBoundaries'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'CellComplex')
		self.outputs.new('SvStringsSocket', 'Faces')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['CellComplex'].sv_set([])
			return
		inputs = self.inputs['CellComplex'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Faces'].sv_set(flatten(outputs))

def register():
	bpy.utils.register_class(SvCellComplexInternalBoundaries)

def unregister():
	bpy.utils.unregister_class(SvCellComplexInternalBoundaries)
