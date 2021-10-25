import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

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
	finalCell = None
	for i in range(len(item)-1):
		cell = topologic.CellUtility.ByLoft([item[i],item[i+1]])
		if finalCell == None:
			finalCell = cell
		else:
			finalCell = finalCell.Union(cell, False)
	return finalCell

class SvCellByLoft(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cell by lofting through the input Wires. The Wires must be closed and ordered
	"""
	bl_idname = 'SvCellByLoft'
	bl_label = 'Cell.ByLoft'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wires')
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		wiresList = self.inputs['Wires'].sv_get(deepcopy=False)
		if isinstance(wiresList[0], list) == False:
			wiresList = [wiresList]
		outputs = []
		for wireList in wiresList:
			outputs.append(processItem(wireList))
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellByLoft)

def unregister():
	bpy.utils.unregister_class(SvCellByLoft)
