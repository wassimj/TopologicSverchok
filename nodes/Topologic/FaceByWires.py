import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	externalBoundary = item[0]
	internalBoundaries = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	if isinstance(item[1], list) == False:
		internalBoundaries = [item[1]]
	else:
		internalBoundaries = item[1]
	for anInternalBoundary in internalBoundaries:
		internalBoundaries.push_back(anInternalBoundary)
	face = topologic.Face.ByExternalInternalBoundaries(externalBoundary, internalBoundaries)
	return face

def recur(input):
	externalBoundary = input[0]
	internalBoundaries = input[1]
	if isinstance(externalBoundary, list):
		for anItem in input:
			output = recur(zip(externalBoundary, internalBoundaries))
	else:
		output = processItem(zip(externalBoundary, internalBoundaries))
	return output
		
class SvFaceByWires(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face from the input planar closed external boundary Wire and a list of planar closed internal boundary wires   
	"""
	bl_idname = 'SvFaceByWires'
	bl_label = 'Face.ByWires'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'External Boundary')
		self.inputs.new('SvStringsSocket', 'Internal Boundaries')
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		ebSocket = self.inputs['External Boundary']
		if not (ebSocket.is_linked):
			return
		else:
			externalBoundaries = ebSocket.sv_get(deepcopy=False)[0]
		ibSocket = self.inputs['Internal Boundaries']
		if ibSocket.is_linked:
			internalBoundaries = ibSocket.sv_get(deepcopy=False) #Should be list of lists. Must be same length as externalBoundary
		else:
			internalBoundaries = []
		outputs = []
		for i in range(len(externalBoundaries)):
			eb = externalBoundaries[i]
			ib = cppyy.gbl.std.list[topologic.Wire.Ptr]()
			for anIB in internalBoundaries:
				if isinstance(anIB, list) == False:
					anIB = [anIB]
				ib.push_back(anIB[0])
			face = topologic.Face.ByExternalInternalBoundaries(eb, ib)
			outputs.append([face])
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceByWires)

def unregister():
	bpy.utils.unregister_class(SvFaceByWires)
