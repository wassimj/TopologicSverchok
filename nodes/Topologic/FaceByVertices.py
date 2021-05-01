import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(vertices):
	stl_vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	for v in vertices:
		stl_vertices.push_back(v)
	return topologic.FaceUtility.ByVertices(stl_vertices)
		
class SvFaceByVertices(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face from the input set of Vertices   
	"""
	bl_idname = 'SvFaceByVertices'
	bl_label = 'Face.ByVertices'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertices')
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		verticesList = self.inputs['Vertices'].sv_get(deepcopy=False)
		if isinstance(verticesList[0], list) == False:
			verticesList = [verticesList]
		outputs = []
		for vertices in verticesList:
			vertices = flatten(vertices)
			if len(vertices) < 3:
				raise Exception("Error: Face.ByVertices - Cannot create a Face because the number of Vertices is less than 3.")
			outputs.append(processItem(vertices))
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceByVertices)

def unregister():
	bpy.utils.unregister_class(SvFaceByVertices)
