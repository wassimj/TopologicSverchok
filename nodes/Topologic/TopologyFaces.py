import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item):
	topologyFaces = []
	faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	_ = item.Faces(faces)
	for aFace in faces:
		topologyFaces.append(aFace)
	return topologyFaces

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output = recur(anItem)
	else:
		output = processItem(input)
	return output
		
class SvTopologyFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Faces of the input Topology    
	"""
	bl_idname = 'SvTopologyFaces'
	bl_label = 'Topology.Faces'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Faces')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Faces'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			print(anInput)
			outputs.append(recur(anInput))
		self.outputs['Faces'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyFaces)

def unregister():
	bpy.utils.unregister_class(SvTopologyFaces)
