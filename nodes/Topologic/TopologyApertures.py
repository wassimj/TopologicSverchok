import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	apertures = []
	apTopologies = []
	_ = item.Apertures(apertures)
	for aperture in apertures:
		apTopologies.append(topologic.Aperture.Topology(aperture))
	return [apertures, apTopologies]
		
class SvTopologyApertures(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Apertures of the input Topology    
	"""
	bl_idname = 'SvTopologyApertures'
	bl_label = 'Topology.Apertures'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Apertures')
		self.outputs.new('SvStringsSocket', 'Aperture Topologies')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Apertures'].sv_set([])
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		topologyList = flatten(topologyList)
		apertures = []
		apTopologies = []
		for anInput in topologyList:
			output = processItem(anInput)
			apertures.append(output[0])
			apTopologies.append(output[1])
		self.outputs['Apertures'].sv_set(apertures)
		self.outputs['Aperture Topologies'].sv_set(apTopologies)

def register():
	bpy.utils.register_class(SvTopologyApertures)

def unregister():
	bpy.utils.unregister_class(SvTopologyApertures)
