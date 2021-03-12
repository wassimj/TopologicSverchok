import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	coords = None
	try:
		x = item.X()
		y = item.Y()
		z = item.Z()
		coords = [x,y,z]
	except:
		coords = None
	return coords

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem(input)
	return output

class SvVertexCoordinates(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the coordinates of the input Vertex    
	"""
	bl_idname = 'SvVertexCoordinates'
	bl_label = 'Vertex.Coordinates'
	Coordinates:StringProperty(name="Coordinates", update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.outputs.new('SvStringsSocket', 'Coordinates').prop_name="Coordinates"


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Coordinates'].sv_set([])
			return
		inputs = self.inputs['Vertex'].sv_get(deepcopy=False)
		outputs = recur(inputs)	
		self.outputs['Coordinates'].sv_set(outputs)


def register():
	bpy.utils.register_class(SvVertexCoordinates)

def unregister():
	bpy.utils.unregister_class(SvVertexCoordinates)
