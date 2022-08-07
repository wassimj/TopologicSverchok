import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import warnings
from . import Replication

def processItem(item):
	cells, tol = item
	assert isinstance(cells, list), "CellComplex.ByCells - Error: Input is not a list"
	cells = [x for x in cells if isinstance(x, topologic.Cell)]
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

def recur(item, tolerance):
	output = []
	if item == None:
		return []
	if isinstance(item[0], list):
		for subItem in item:
			output.append(recur(subItem, tolerance))
	else:
		output = processItem([item, tolerance])
	return output

class SvCellComplexByCells(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a CellComplex from the list of input Cells  
	"""
	bl_idname = 'SvCellComplexByCells'
	bl_label = 'CellComplex.ByCells'
	bl_icon = 'SELECT_DIFFERENCE'

	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cells')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'CellComplex')
		self.width = 175
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['CellComplex'].sv_set([])
			return
		cellList = self.inputs['Cells'].sv_get(deepcopy=False)
		tolerance = self.inputs['Tol'].sv_get(deepcopy=False)[0][0]
		output = recur(cellList, tolerance)
		if isinstance(output, list) == False:
			output = [output]
		self.outputs['CellComplex'].sv_set(output)

def register():
    bpy.utils.register_class(SvCellComplexByCells)

def unregister():
    bpy.utils.unregister_class(SvCellComplexByCells)
