import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import cppyy
import time


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
	direct = item[1]
	viaSharedTopologies = item[2]
	viaSharedApertures = item[3]
	toExteriorTopologies = item[4]
	toExteriorApertures = item[5]
	useInternalVertex = item[6]
	tolerance = item[7]
	graph = None
	try:
		graph = Graph.ByTopology(topology, direct, viaSharedTopologies, viaSharedApertures, toExteriorTopologies, toExteriorApertures, useInternalVertex, tolerance)
	except:
		print("ERROR: (Topologic>Graph.ByTopology) operation failed.")
		graph = None
	return graph

class SvGraphByTopology(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Dual Graph of the input Topology
	"""
	bl_idname = 'SvGraphByTopology'
	bl_label = 'Graph.ByTopology'
	DirectProp: BoolProperty(name="Direct", default=True, update=updateNode)
	ViaSharedTopologiesProp: BoolProperty(name="ViaSharedTopologies", default=False, update=updateNode)
	ViaSharedAperturesProp: BoolProperty(name="ViaSharedApertures", default=False, update=updateNode)
	ToExteriorTopologiesProp: BoolProperty(name="ToExteriorTopoloogies", default=False, update=updateNode)
	ToExteriorAperturesProp: BoolProperty(name="ToExteriorApertures", default=False, update=updateNode)
	UseInternalVertexProp: BoolProperty(name="UseInternalVertex", default=False, update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Direct').prop_name = 'DirectProp'
		self.inputs.new('SvStringsSocket', 'ViaSharedTopologies').prop_name = 'ViaSharedTopologiesProp'
		self.inputs.new('SvStringsSocket', 'ViaSharedApertures').prop_name = 'ViaSharedAperturesProp'
		self.inputs.new('SvStringsSocket', 'ToExteriorTopologies').prop_name = 'ToExteriorTopologiesProp'
		self.inputs.new('SvStringsSocket', 'ToExteriorApertures').prop_name = 'ToExteriorAperturesProp'
		self.inputs.new('SvStringsSocket', 'UseInternalVertex').prop_name = 'UseInternalVertexProp'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Graph')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Graph'].sv_set([])
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		directList = self.inputs['Direct'].sv_get(deepcopy=False)[0]
		viaSharedTopologiesList = self.inputs['ViaSharedTopologies'].sv_get(deepcopy=False)[0]
		viaSharedAperturesList = self.inputs['ViaSharedApertures'].sv_get(deepcopy=False)[0]
		toExteriorTopologiesList = self.inputs['ToExteriorTopologies'].sv_get(deepcopy=False)[0]
		toExteriorAperturesList = self.inputs['ToExteriorApertures'].sv_get(deepcopy=False)[0]
		useInternalVertexList = self.inputs['UseInternalVertex'].sv_get(deepcopy=False)[0]
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=False)[0]

		maxLength = max([len(topologyList), len(directList), len(viaSharedTopologiesList), len(viaSharedAperturesList), len(toExteriorTopologiesList), len(toExteriorAperturesList), len(useInternalVertexList), len(toleranceList)])
		for i in range(len(topologyList), maxLength):
			topologyList.append(topologyList[-1])

		for i in range(len(directList), maxLength):
			directList.append(directList[-1])

		for i in range(len(viaSharedTopologiesList), maxLength):
			viaSharedTopologiesList.append(viaSharedTopologiesList[-1])

		for i in range(len(viaSharedAperturesList), maxLength):
			viaSharedAperturesList.append(viaSharedAperturesList[-1])

		for i in range(len(toExteriorTopologiesList), maxLength):
			toExteriorTopologiesList.append(toExteriorTopologiesList[-1])

		for i in range(len(toExteriorAperturesList), maxLength):
			toExteriorAperturesList.append(toExteriorAperturesList[-1])

		for i in range(len(useInternalVertexList), maxLength):
			useInternalVertexList.append(useInternalVertexList[-1])

		for i in range(len(toleranceList), maxLength):
			toleranceList.append(toleranceList[-1])

		inputs = []
		outputs = []
		if (len(topologyList) == len(directList) == len(viaSharedTopologiesList) == len(viaSharedAperturesList) == len(toExteriorTopologiesList) == len(toExteriorAperturesList) == len(useInternalVertexList) == len(toleranceList)):
			inputs = zip(topologyList, directList, viaSharedTopologiesList, viaSharedAperturesList, toExteriorTopologiesList, toExteriorAperturesList, useInternalVertexList, toleranceList)
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Graph'].sv_set(outputs)
		end = time.time()
		print("Graph.ByTopology Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphByTopology)

def unregister():
    bpy.utils.unregister_class(SvGraphByTopology)
