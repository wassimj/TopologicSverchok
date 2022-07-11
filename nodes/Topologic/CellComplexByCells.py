import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty
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

def list_level_iter(lst, level, _current_level: int= 1):
    """
    Iterate over all lists with given nesting
    With level 1 it will return the given list
    With level 2 it will iterate over all nested lists in the main one
    If a level does not have lists on that level it will return empty list
    _current_level - for internal use only
    """
    if _current_level < level:
        try:
            for nested_lst in lst:
                if not isinstance(nested_lst, list):
                    raise TypeError
                yield from list_level_iter(nested_lst, level, _current_level + 1)
        except TypeError:
            yield []
    else:
        yield lst

def processItem(cells, tol):
	cellComplex = topologic.CellComplex.ByCells(cells, tol)
	if not cellComplex:
		warnings.warn("Warning: Default CellComplex.ByCells method failed. Attempting to Merge the Cells.", UserWarning)
		result = cells[0]
		remainder = cells[1:]
		cluster = topologic.Cluster.ByTopologies(remainder, False)
		result = result.Merge(cluster, False)
		if result.Type() != 64: #64 is the type of a CellComplex
			warnings.warn("Warning: Input Cells do not form a CellComplex", UserWarning)
			if result.Type() > 64:
				returnCellComplexes = []
				_ = result.CellComplexes(None, returnCellComplexes)
				return returnCellComplexes
			else:
				return None
	else:
		return cellComplex

class SvCellComplexByCells(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a CellComplex from the list of input Cells  
	"""
	bl_idname = 'SvCellComplexByCells'
	bl_label = 'CellComplex.ByCells'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)
	Level: IntProperty(name='Level', default =1,min=1, update = updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cells')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.inputs.new('SvStringsSocket', 'Level').prop_name='Level'
		self.outputs.new('SvStringsSocket', 'CellComplex')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		cellList = self.inputs['Cells'].sv_get(deepcopy=False)
		level = flatten(self.inputs['Level'].sv_get(deepcopy=False, default= 1))
		tol = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)[0][0]
		if isinstance(level,list):
			level = int(level[0])
		cellList = list(list_level_iter(cellList,level))
		cellList = [flatten(t) for t in cellList]
		outputs = []
		for t in range(len(cellList)):
			outputs.append(processItem(cellList[t], tol))
		self.outputs['CellComplex'].sv_set(outputs)
		end = time.time()
		print("CellComplex.ByCells Operation consumed "+str(round(end - start,2)*1000)+" ms")

def register():
    bpy.utils.register_class(SvCellComplexByCells)

def unregister():
    bpy.utils.unregister_class(SvCellComplexByCells)
