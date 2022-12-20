import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty
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
	vertex = item[1]
	tolerance = item[2]
	status = False
	if topology.Type() == topologic.Cell.Type():
		status = (topologic.CellUtility.Contains(topology, vertex, tolerance) == 0)
	return status

class SvCellIsInside(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Returns True if the input Vertex is inside the input Cell. Returns False otherwise
	"""
	bl_idname = 'SvCellIsInside'
	bl_label = 'Cell.IsInside'
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cell')
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Is Inside')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		cells = self.inputs['Cell'].sv_get(deepcopy=False)
		cells = flatten(cells)
		vertices = self.inputs['Vertex'].sv_get(deepcopy=False)
		vertices = flatten(vertices)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=False)[0]
		outputs = []
		maxLength = max([len(cells), len(vertices), len(toleranceList)])
		for i in range(len(cells), maxLength):
			cells.append(cells[-1])
		for i in range(len(vertices), maxLength):
			vertices.append(vertices[-1])
		for i in range(len(toleranceList), maxLength):
			toleranceList.append(toleranceList[-1])
		inputs = zip(cells, vertices, toleranceList)
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Is Inside'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellIsInside)

def unregister():
	bpy.utils.unregister_class(SvCellIsInside)
