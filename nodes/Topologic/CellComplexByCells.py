import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import time
import warnings

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(cells):
	cellComplex = cells[0]
	gc = topologic.GlobalCluster.GetInstance()
	subTopologies = []
	for i in range(1,len(cells)):
		try:
			cellComplex = cellComplex.Merge(cells[i], False)
			gc.RemoveTopology(cellComplex)
		except:
			raise Exception("Error: CellComplex.ByCells operation failed during processing the input Cells")
	if cellComplex.Type() != 64: #64 is the type of a CellComplex
		warnings.warn("Warning: Input Cells do not form a CellComplex", UserWarning)
	gc.AddTopology(cellComplex)
	return cellComplex

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
		cellsList = self.inputs['Cells'].sv_get(deepcopy=False)
		if isinstance(cellsList[0], list) == False:
			cellsList = [cellsList]
		outputs = []
		for cells in cellsList:
			outputs.append(processItem(cells))
		self.outputs['CellComplex'].sv_set(outputs)
		end = time.time()
		print("CellComplex.ByCells Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvCellComplexByCells)

def unregister():
    bpy.utils.unregister_class(SvCellComplexByCells)
