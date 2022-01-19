import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time

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
	outerWalls = []
	innerWalls = []
	roofs = []
	floors = []
	slabs = []

	faces = []
	_ = item.Faces(None, faces)
	for aFace in faces:
		z = topologic.FaceUtility.NormalAtParameters(aFace, 0.5, 0.5)[2]
		cells = []
		aFace.Cells(item, cells)
		n = len(cells)
		if abs(z) < 0.001:
			if n == 1:
				outerWalls.append(aFace)
			else:
				innerWalls.append(aFace)
		elif n == 1:
			if z > 0.9:
				roofs.append(aFace)
			elif z < -0.9:
				floors.append(aFace)
		else:
			slabs.append(aFace)
	return [outerWalls, innerWalls, roofs, floors, slabs]

class SvCellComplexDecompose(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a list of categorised boundaries (Faces) of the input CellComplex    
	"""
	bl_idname = 'SvCellComplexDecompose'
	bl_label = 'CellComplex.Decompose'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'CellComplex')
		self.outputs.new('SvStringsSocket', 'Outer Wall')
		self.outputs.new('SvStringsSocket', 'Inner Wall')
		self.outputs.new('SvStringsSocket', 'Roof')
		self.outputs.new('SvStringsSocket', 'Floor')
		self.outputs.new('SvStringsSocket', 'Slab')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['CellComplex'].sv_set([])
			return
		inputs = self.inputs['CellComplex'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outerWalls = []
		innerWalls = []
		roofs = []
		floors = []
		slabs = []
		for anInput in inputs:
			outerWalls.append(processItem(anInput)[0])
			innerWalls.append(processItem(anInput)[1])
			roofs.append(processItem(anInput)[2])
			floors.append(processItem(anInput)[3])
			slabs.append(processItem(anInput)[4])
		self.outputs['Outer Wall'].sv_set(flatten(outerWalls))
		self.outputs['Inner Wall'].sv_set(flatten(innerWalls))
		self.outputs['Roof'].sv_set(flatten(roofs))
		self.outputs['Floor'].sv_set(flatten(floors))
		self.outputs['Slab'].sv_set(flatten(slabs))


def register():
	bpy.utils.register_class(SvCellComplexDecompose)

def unregister():
	bpy.utils.unregister_class(SvCellComplexDecompose)
