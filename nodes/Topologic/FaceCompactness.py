import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import math

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
	exb = item.ExternalBoundary()
	edges = []
	_ = exb.Edges(edges)
	perimeter = 0.0
	for anEdge in edges:
		perimeter = perimeter + abs(topologic.EdgeUtility.Length(anEdge))
	area = abs(topologic.FaceUtility.Area(item))
	compactness  = 0
	#From https://en.wikipedia.org/wiki/Compactness_measure_of_a_shape

	if area <= 0:
		raise Exception("Error: Face.Compactness: Face area is less than or equal to zero")
	if perimeter <= 0:
		raise Exception("Error: Face.Compactness: Face perimeter is less than or equal to zero")
	compactness = (math.pi*(2*math.sqrt(area/math.pi)))/perimeter
	return compactness
		
class SvFaceCompactness(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the compactness (isoperimetric quotient) measure of the input Face    
	"""
	bl_idname = 'SvFaceCompactness'
	bl_label = 'Face.Compactness'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Compactness')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Face'].sv_get(deepcopy=True)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Compactness'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceCompactness)

def unregister():
	bpy.utils.unregister_class(SvFaceCompactness)
