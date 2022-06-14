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

def getApertures(topology):
	apertures = []
	apTopologies = []
	_ = topology.Apertures(apertures)
	for aperture in apertures:
		apTopologies.append(topologic.Aperture.Topology(aperture))
	return apTopologies

def processItem(item):
	externalVerticalFaces = []
	internalVerticalFaces = []
	topHorizontalFaces = []
	bottomHorizontalFaces = []
	internalHorizontalFaces = []
	externalVerticalApertures = []
	internalVerticalApertures = []
	topHorizontalApertures = []
	bottomHorizontalApertures = []
	internalHorizontalApertures = []

	faces = []
	_ = item.Faces(None, faces)
	for aFace in faces:
		z = topologic.FaceUtility.NormalAtParameters(aFace, 0.5, 0.5)[2]
		cells = []
		aFace.Cells(item, cells)
		n = len(cells)
		if abs(z) < 0.001:
			if n == 1:
				externalVerticalFaces.append(aFace)
				externalVerticalApertures.append(getApertures(aFace))
			else:
				internalVerticalFaces.append(aFace)
				internalVerticalApertures.append(getApertures(aFace))
		elif n == 1:
			if z > 0.9:
				topHorizontalFaces.append(aFace)
				topHorizontalApertures.append(getApertures(aFace))
			elif z < -0.9:
				bottomHorizontalFaces.append(aFace)
				bottomHorizontalApertures.append(getApertures(aFace))

		else:
			internalHorizontalFaces.append(aFace)
			internalHorizontalApertures.append(getApertures(aFace))
	return1 = []
	return2 = []
	return3 = []
	return4 = []
	return5 = []
	return6 = []
	return7 = []
	return8 = []
	return9 = []
	return10 = []
	if len(externalVerticalFaces) > 0:
		return1 = flatten(externalVerticalFaces)
	if len(internalVerticalFaces) > 0:
		return2 = flatten(internalVerticalFaces)
	if len(topHorizontalFaces) > 0:
		return3 = flatten(topHorizontalFaces)
	if len(bottomHorizontalFaces) > 0:
		return4 = flatten(bottomHorizontalFaces)
	if len(internalHorizontalFaces) > 0:
		return5 = flatten(internalHorizontalFaces)
	if len(externalVerticalApertures) > 0:
		return6 = flatten(externalVerticalApertures)
	if len(internalVerticalApertures) > 0:
		return7 = flatten(internalVerticalApertures)
	if len(topHorizontalApertures) > 0:
		return8 = flatten(topHorizontalApertures)
	if len(bottomHorizontalApertures) > 0:
		return9 = flatten(bottomHorizontalApertures)
	if len(internalHorizontalApertures) > 0:
		return10 = flatten(internalHorizontalApertures)

	return [return1, return2, return3, return4, return5, return6, return7, return8, return9, return10]

class SvCellComplexDecompose(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a list of categorised boundaries (Faces) of the input CellComplex    
	"""
	bl_idname = 'SvCellComplexDecompose'
	bl_label = 'CellComplex.Decompose'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'CellComplex')
		self.outputs.new('SvStringsSocket', 'External Vertical Faces')
		self.outputs.new('SvStringsSocket', 'Internal Vertical Faces')
		self.outputs.new('SvStringsSocket', 'Top Horizontal Faces')
		self.outputs.new('SvStringsSocket', 'Bottom Horizontal Faces')
		self.outputs.new('SvStringsSocket', 'Internal Horizontal Faces')
		self.outputs.new('SvStringsSocket', 'External Vertical Apertures')
		self.outputs.new('SvStringsSocket', 'Internal Vertical Apertures')
		self.outputs.new('SvStringsSocket', 'Top Horizontal Apertures')
		self.outputs.new('SvStringsSocket', 'Bottom Horizontal Apertures')
		self.outputs.new('SvStringsSocket', 'Internal Horizontal Apertures')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['CellComplex'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		externalVerticalFaces = []
		internalVerticalFaces = []
		topHorizontalFaces = []
		bottomHorizontalFaces = []
		internalHorizontalFaces = []
		externalVerticalApertures = []
		internalVerticalApertures = []
		topHorizontalApertures = []
		bottomHorizontalApertures = []
		internalHorizontalApertures = []
		for anInput in inputs:
			output = processItem(anInput)
			externalVerticalFaces.append(output[0])
			internalVerticalFaces.append(output[1])
			topHorizontalFaces.append(output[2])
			bottomHorizontalFaces.append(output[3])
			internalHorizontalFaces.append(output[4])
			externalVerticalApertures.append(output[5])
			internalVerticalApertures.append(output[6])
			topHorizontalApertures.append(output[7])
			bottomHorizontalApertures.append(output[8])
			internalHorizontalApertures.append(output[9])
		self.outputs['External Vertical Faces'].sv_set(flatten(externalVerticalFaces))
		self.outputs['Internal Vertical Faces'].sv_set(flatten(internalVerticalFaces))
		self.outputs['Top Horizontal Faces'].sv_set(flatten(topHorizontalFaces))
		self.outputs['Bottom Horizontal Faces'].sv_set(flatten(bottomHorizontalFaces))
		self.outputs['Internal Horizontal Faces'].sv_set(flatten(internalHorizontalFaces))
		self.outputs['External Vertical Apertures'].sv_set(flatten(externalVerticalApertures))
		self.outputs['Internal Vertical Apertures'].sv_set(flatten(internalVerticalApertures))
		self.outputs['Top Horizontal Apertures'].sv_set(flatten(topHorizontalApertures))
		self.outputs['Bottom Horizontal Apertures'].sv_set(flatten(bottomHorizontalApertures))
		self.outputs['Internal Horizontal Apertures'].sv_set(flatten(internalHorizontalApertures))


def register():
	bpy.utils.register_class(SvCellComplexDecompose)

def unregister():
	bpy.utils.unregister_class(SvCellComplexDecompose)
