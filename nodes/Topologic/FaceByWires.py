import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	print(item)
	externalBoundary = item[0]
	internalBoundaries = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	for ib in item[1]:
		internalBoundaries.push_back(ib)
	print(item[0])
	print(item[1])
	face = topologic.Face.ByExternalInternalBoundaries(externalBoundary, internalBoundaries)
	return face

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
			externalBoundaries = ebSocket.sv_get(deepcopy=False)
		ibSocket = self.inputs['Internal Boundaries']
		if ibSocket.is_linked:
			internalBoundaries = ibSocket.sv_get(deepcopy=False) #Should be list of lists. Must be same length as externalBoundary
			if isinstance(internalBoundaries[0], list) == False:
				internalBoundaries = [internalBoundaries]
		else:
			internalBoundaries = []
		if (len(externalBoundaries) != len(internalBoundaries)) and len(internalBoundaries) > 0:
			return
		print(externalBoundaries)
		print(internalBoundaries)
		inputs = zip(externalBoundaries, internalBoundaries)
		outputs = []
		for anInput in inputs:
			outputs.append(recur(anInput))
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceByWires)

def unregister():
	bpy.utils.unregister_class(SvFaceByWires)
