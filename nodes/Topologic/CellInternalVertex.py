import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

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
	topology = item[0]
	tolerance = item[1]
	vert = None
	if topology.Type() == topologic.Cell.Type():
		vert = topologic.CellUtility.InternalVertex(topology, tolerance)
	return vert

class SvCellInternalVertex(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a Vertex guaranteed to be inside the input Cell
	"""
	bl_idname = 'SvCellInternalVertex'
	bl_label = 'Cell.InternalVertex'
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cell')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Vertex')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		cells = self.inputs['Cell'].sv_get(deepcopy=False)
		cells = flatten(cells)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=False)[0]
		outputs = []
		maxLength = max([len(cells), len(toleranceList)])
		for i in range(len(cells), maxLength):
			cells.append(cells[-1])
		for i in range(len(toleranceList), maxLength):
			toleranceList.append(toleranceList[-1])
		inputs = zip(cells, toleranceList)
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Vertex'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellInternalVertex)

def unregister():
	bpy.utils.unregister_class(SvCellInternalVertex)
