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
	origin = item[1]
	x = item[2]
	y = item[3]
	z = item[4]
	degree = item[5]
	return fixTopologyClass(topologic.TopologyUtility.Rotate(topology, origin, x, y, z, degree))
		
class SvTopologyRotate(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Rotates the input Topology based on the input rotation origin, axis of rotation, and degrees    
	"""
	bl_idname = 'SvTopologyRotate'
	bl_label = 'Topology.Rotate'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=1, precision=4, update=updateNode)
	Degree: FloatProperty(name="Degree",  default=0, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.inputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.inputs.new('SvStringsSocket', 'Z').prop_name = 'Z'
		self.inputs.new('SvStringsSocket', 'Degree').prop_name = 'Degree'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		origins = []
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		if (self.inputs['Origin'].is_linked):
			origins = self.inputs['Origin'].sv_get(deepcopy=False)
		else:
			for anInput in inputs:
				origins.append(anInput.Centroid())
		xCoords = self.inputs['X'].sv_get(deepcopy=False)[0]
		yCoords = self.inputs['Y'].sv_get(deepcopy=False)[0]
		zCoords = self.inputs['Z'].sv_get(deepcopy=False)[0]
		degrees = self.inputs['Degree'].sv_get(deepcopy=False)[0]
		maxLength = max([len(inputs), len(origins), len(xCoords), len(yCoords), len(zCoords), len(degrees)])
		for i in range(len(inputs), maxLength):
			inputs.append(inputs[-1])
		for i in range(len(origins), maxLength):
			origins.append(origins[-1])
		for i in range(len(xCoords), maxLength):
			xCoords.append(xCoords[-1])
		for i in range(len(yCoords), maxLength):
			yCoords.append(yCoords[-1])
		for i in range(len(zCoords), maxLength):
			zCoords.append(zCoords[-1])
		for i in range(len(degrees), maxLength):
			degrees.append(degrees[-1])
		if (len(inputs) == len(origins) == len(xCoords) == len(yCoords) == len(zCoords) == len(degrees)):
			newInputs = zip(inputs, origins, xCoords, yCoords, zCoords, degrees)
		outputs = []
		for anInput in newInputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyRotate)

def unregister():
	bpy.utils.unregister_class(SvTopologyRotate)
