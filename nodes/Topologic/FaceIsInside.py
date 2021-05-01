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
	if topology.Type() == topologic.Face.Type():
		status = (topologic.FaceUtility.IsInside(topology, vertex, tolerance))
	return status

class SvFaceIsInside(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the input Vertex is inside the input Face. Returns False otherwise
	"""
	bl_idname = 'SvFaceIsInside'
	bl_label = 'Face.IsInside'
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Is Inside')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		cells = self.inputs['Face'].sv_get(deepcopy=False)
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
	bpy.utils.register_class(SvFaceIsInside)

def unregister():
	bpy.utils.unregister_class(SvFaceIsInside)
