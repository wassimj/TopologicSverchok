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
	newTopology = None
	try:
		newTopology = fixTopologyClass(topologic.TopologyUtility.Scale(topology, origin, x, y, z))
	except:
		print("ERROR: (Topologic>TopologyUtility.Rotate) operation failed.")
		newTopology = None
	return newTopology

		
class SvTopologyScale(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Scales the input Topology based on the input origin, and X, Y, Z scale factors    
	"""
	bl_idname = 'SvTopologyScale'
	bl_label = 'Topology.Scale'
	XFactor: FloatProperty(name="XFactor", default=1, precision=4, update=updateNode)
	YFactor: FloatProperty(name="YFactor",  default=1, precision=4, update=updateNode)
	ZFactor: FloatProperty(name="ZFactor",  default=1, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'XFactor').prop_name = 'XFactor'
		self.inputs.new('SvStringsSocket', 'YFactor').prop_name = 'YFactor'
		self.inputs.new('SvStringsSocket', 'ZFactor').prop_name = 'ZFactor'
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
		xFactors = self.inputs['XFactor'].sv_get(deepcopy=False)[0]
		yFactors = self.inputs['YFactor'].sv_get(deepcopy=False)[0]
		zFactors = self.inputs['ZFactor'].sv_get(deepcopy=False)[0]
		maxLength = max([len(inputs), len(origins), len(xFactors), len(yFactors), len(zFactors)])
		for i in range(len(inputs), maxLength):
			inputs.append(inputs[-1])
		for i in range(len(origins), maxLength):
			origins.append(origins[-1])
		for i in range(len(xFactors), maxLength):
			xFactors.append(xFactors[-1])
		for i in range(len(yFactors), maxLength):
			yFactors.append(yFactors[-1])
		for i in range(len(zFactors), maxLength):
			zFactors.append(zFactors[-1])
		if (len(inputs) == len(origins) == len(xFactors) == len(yFactors) == len(zFactors)):
			newInputs = zip(inputs, origins, xFactors, yFactors, zFactors)
		outputs = []
		for anInput in newInputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyScale)

def unregister():
	bpy.utils.unregister_class(SvTopologyScale)
