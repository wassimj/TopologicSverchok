import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

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
	edges = []
	_ = item.Edges(None, edges)
	obEdges = []
	for anEdge in edges:
		faces = []
		_ = anEdge.Faces(item, faces)
		if len(faces) == 1:
			obEdges.append(anEdge)
	returnTopology = None
	try:
		returnTopology = topologic.Wire.ByEdges(obEdges)
	except:
		returnTopology = topologic.Cluster.ByTopologies(obEdges)
		returnTopology = returnTopology.SelfMerge()
	return returnTopology

class SvShellExternalBoundary(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the external boundary (Wire) of the input Shell    
	"""
	bl_idname = 'SvShellExternalBoundary'
	bl_label = 'Shell.ExternalBoundary'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Shell')
		self.outputs.new('SvStringsSocket', 'Boundary')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Wire'].sv_set([])
			return
		inputs = self.inputs['Shell'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Boundary'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvShellExternalBoundary)

def unregister():
	bpy.utils.unregister_class(SvShellExternalBoundary)
