import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy
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
	print(item)
	cellComplex = None
	cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
	for aCell in item:
		cells.push_back(aCell)
	cellComplex = topologic.CellComplex.ByCells(cells)
	return cellComplex

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input[0], list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem(input)
	return output

class SvCellComplexByCells(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a CellComplex from the list of input Cells  
	"""
	bl_idname = 'SvCellComplexByCells'
	bl_label = 'CellComplex.ByCells'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cells')
		self.outputs.new('SvStringsSocket', 'CellComplex')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Cells'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		cellComplex = processItem(inputs)
		self.outputs['CellComplex'].sv_set([cellComplex])
		end = time.time()
		print("CellComplex.ByCells Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvCellComplexByCells)

def unregister():
    bpy.utils.unregister_class(SvCellComplexByCells)
