import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import math

def processItem(item):
	faces = []
	_ = item.Faces(None, faces)
	area = 0.0
	for aFace in faces:
		area = area + abs(topologic.FaceUtility.Area(aFace))
	volume = abs(topologic.CellUtility.Volume(item))
	compactness  = 0
	#From https://en.wikipedia.org/wiki/Sphericity
	if area > 0:
		compactness = (((math.pi)**(1/3))*((6*volume)**(2/3)))/area
	else:
		raise Exception("Error: Cell.Compactness: Cell surface area is not positive")
	return compactness

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
		
class SvCellCompactness(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the compactness (sphericity) measure of the input Cell    
	"""
	bl_idname = 'SvCellCompactness'
	bl_label = 'Cell.Compactness'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cell')
		self.outputs.new('SvStringsSocket', 'Compactness')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Cell'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Compactness'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellCompactness)

def unregister():
	bpy.utils.unregister_class(SvCellCompactness)
