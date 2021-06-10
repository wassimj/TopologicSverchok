import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	_ = item.Faces(faces)
	area = 0.0
	for aFace in faces:
		area = area + topologic.FaceUtility.Area(aFace)
	return area

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
		
class SvCellSurfaceArea(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the surface area of the input Cell    
	"""
	bl_idname = 'SvCellSurfaceArea'
	bl_label = 'Cell.SurfaceArea'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cell')
		self.outputs.new('SvStringsSocket', 'Area')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Cell'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Area'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellSurfaceArea)

def unregister():
	bpy.utils.unregister_class(SvCellSurfaceArea)
