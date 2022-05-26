import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from molior import Molior

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
    molior_object = Molior.from_cellcomplex(cellcomplex=item, file=None, name="Homemaker building")
    molior_object.execute()
    return molior_object.file

class SvHMIFCByCellComplex(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a Homemaker IFC of the input CellComplex    
	"""
	bl_idname = 'SvHMIFCByCellComplex'
	bl_label = 'Homemaker.IFCByCellComplex'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'CellComplex')
		self.outputs.new('SvStringsSocket', 'IFC')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['IFC'].sv_set([])
			return
		inputs = self.inputs['CellComplex'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['IFC'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvHMIFCByCellComplex)

def unregister():
	bpy.utils.unregister_class(SvHMIFCByCellComplex)
