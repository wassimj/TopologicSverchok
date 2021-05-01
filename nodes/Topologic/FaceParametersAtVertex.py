import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary, Aperture
import cppyy
import time
import ctypes

def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def matchLengths(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

def classByType(argument):
	switcher = {
		1: Vertex,
		2: Edge,
		4: Wire,
		8: Face,
		16: Shell,
		32: Cell,
		64: CellComplex,
		128: Cluster }
	return switcher.get(argument, Topology)

def fixTopologyClass(topology):
  topology.__class__ = classByType(topology.GetType())
  return topology

def processItem(item):
	face = item[0]
	vertex = item[1]
	u = ctypes.c_double() 
	v = ctypes.c_double() 
	print(face)
	print(vertex)
	_ = topologic.FaceUtility.ParametersAtVertex(face, vertex, u, v)
	print([u.value, v.value])
	return [u.value, v.value]

class SvFaceParametersAtVertex(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the UV parameters of the input Vertex within the input Face    
	"""
	bl_idname = 'SvFaceParametersAtVertex'
	bl_label = 'Face.ParametersAtVertex'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.outputs.new('SvStringsSocket', 'UV').prop_name = 'U'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['UV'].sv_set([])
			return
		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		vertexList = self.inputs['Vertex'].sv_get(deepcopy=False)

		faceList = flatten(faceList)
		vertexList = flatten(vertexList)
		matchLengths([faceList, vertexList])
		inputs = zip(faceList, vertexList)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['UV'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceParametersAtVertex)

def unregister():
	bpy.utils.unregister_class(SvFaceParametersAtVertex)
