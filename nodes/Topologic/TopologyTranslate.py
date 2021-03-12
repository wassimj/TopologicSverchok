import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import cppyy

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
	topology = item[0]
	x = item[1]
	y = item[2]
	z = item[3]
	newTopology = None
	try:
		newTopology = fixTopologyClass(topologic.TopologyUtility.Translate(topology, x, y, z))
	except:
		print("ERROR: (Topologic>TopologyUtility.Translate) operation failed.")
		newTopology = None
	return newTopology

		
class SvTopologyTranslate(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Translates the input Topology based on the input X,Y,Z translation values    
	"""
	bl_idname = 'SvTopologyTranslate'
	bl_label = 'Topology.Translate'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=0, precision=4, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.inputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.inputs.new('SvStringsSocket', 'Z').prop_name = 'Z'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		xCoords = self.inputs['X'].sv_get(deepcopy=False)[0]
		yCoords = self.inputs['Y'].sv_get(deepcopy=False)[0]
		zCoords = self.inputs['Z'].sv_get(deepcopy=False)[0]
		maxLength = max([len(inputs), len(xCoords), len(yCoords), len(zCoords)])
		for i in range(len(inputs), maxLength):
			inputs.append(inputs[-1])
		for i in range(len(xCoords), maxLength):
			xCoords.append(xCoords[-1])
		for i in range(len(yCoords), maxLength):
			yCoords.append(yCoords[-1])
		for i in range(len(zCoords), maxLength):
			zCoords.append(zCoords[-1])
		if (len(inputs) == len(xCoords) == len(yCoords) == len(zCoords)):
			newInputs = zip(inputs, xCoords, yCoords, zCoords)
		outputs = []
		for anInput in newInputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyTranslate)

def unregister():
	bpy.utils.unregister_class(SvTopologyTranslate)
