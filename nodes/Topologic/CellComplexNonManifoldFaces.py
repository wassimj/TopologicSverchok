import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item):
	faces = []
	_ = item.NonManifoldFaces(faces)
	return faces

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

class SvCellComplexNonManifoldFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the non-manifold Faces of the input CellComplex    
	"""
	bl_idname = 'SvCellComplexNonManifoldFaces'
	bl_label = 'CellComplex.NonManifoldFaces'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'CellComplex')
		self.outputs.new('SvStringsSocket', 'Faces')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Cell'].sv_set([])
			return
		inputs = self.inputs['CellComplex'].sv_get(deepcopy=False)
		outputs = recur(inputs)
		if (len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['Faces'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellComplexNonManifoldFaces)

def unregister():
	bpy.utils.unregister_class(SvCellComplexNonManifoldFaces)
