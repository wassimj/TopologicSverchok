import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

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
	topology = None
	file = open(item)
	brepString = file.read()
	topology = fixTopologyClass(topologic.Topology.DeepCopy(Topology.ByString(brepString)))
	file.close()
	return topology
		
class SvTopologyByImportedBRep(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology from the input BREP file
	"""
	bl_idname = 'SvTopologyByImportedBRep'
	bl_label = 'Topology.ByImportedBRep'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'File Path')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		inputs = self.inputs['File Path'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyByImportedBRep)

def unregister():
	bpy.utils.unregister_class(SvTopologyByImportedBRep)
