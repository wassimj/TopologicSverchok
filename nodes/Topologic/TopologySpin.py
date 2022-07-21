import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from . import Replication, ShellByLoft, CellComplexByLoft, TopologySelfMerge, WireByVertices

def processItem(item):
	topology, \
	origin, \
	dirX, \
	dirY, \
	dirZ, \
	degree, \
	sides, \
	tolerance = item
	topologies = []
	unit_degree = degree / float(sides)
	for i in range(sides+1):
		topologies.append(topologic.TopologyUtility.Rotate(topology, origin, dirX, dirY, dirZ, unit_degree*i))
	returnTopology = None
	if topology.Type() == topologic.Vertex.Type():
		returnTopology = WireByVertices.processItem([topologies, False])
	elif topology.Type() == topologic.Edge.Type():
		try:
			returnTopology = ShellByLoft.processItem([topologies, tolerance])
		except:
			try:
				returnTopology = topologic.Cluster.ByTopologies(topologies)
			except:
				returnTopology = None
	elif topology.Type() == topologic.Wire.Type():
		if topology.IsClosed():
			try:
				returnTopology = CellByLoft.processItem([topologies, tolerance])
			except:
				try:
					returnTopology = CellComplexByLoft.processItem(topologies, tolerance)
					try:
						returnTopology = returnTopology.ExternalBoundary()
					except:
						pass
				except:
					try:
						returnTopology = ShellByLoft.processItem([topologies, tolerance])
					except:
						try:
							returnTopology = topologic.Cluster.ByTopologies(topologies)
						except:
							returnTopology = None
		else:
			try:
				returnTopology = ShellByLoft.processItem([topologies, tolerance])
			except:
				try:
					returnTopology = topologic.Cluster.ByTopologies(topologies)
				except:
					returnTopology = None
	elif topology.Type() == topologic.Face.Type():
		external_wires = []
		for t in topologies:
			external_wires.append(topologic.Face.ExternalBoundary(t))
		try:
			returnTopology = CellComplexByLoft.processItem([external_wires, tolerance])
		except:
			try:
				returnTopology = ShellByLoft.processItem([external_wires, tolerance])
			except:
				try:
					returnTopology = topologic.Cluster.ByTopologies(topologies)
				except:
					returnTopology = None
	else:
		returnTopology = TopologySelfMerge.processItem(topologic.Cluster.ByTopologies(topologies))
	if returnTopology.Type() == topologic.Shell.Type():
		try:
			new_t = topologic.Cell.ByShell(returnTopology)
			if new_t:
				returnTopology = new_t
		except:
			pass
	return returnTopology

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvTopologySpin(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Spins the input Wire based on the input number of sides, rotation origin, axis of rotation, and degrees    
	"""
	bl_idname = 'SvTopologySpin'
	bl_label = 'Topology.Spin'
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y",  default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z",  default=1, precision=4, update=updateNode)
	Degree: FloatProperty(name="Degree",  default=0, precision=4, update=updateNode)
	Sides: IntProperty(name="Sides", default=16, min=1, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.inputs.new('SvStringsSocket', 'Degree').prop_name = 'Degree'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'Sides'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		originList = []
		if not any(socket.is_linked for socket in self.outputs):
			return
		wireList = self.inputs['Topology'].sv_get(deepcopy=True)
		wireList = Replication.flatten(wireList)
		if (self.inputs['Origin'].is_linked):
			originList = self.inputs['Origin'].sv_get(deepcopy=True)
			originList = Replication.flatten(originList)
		else:
			originList = []
			for aTopology in wireList:
				originList.append(aTopology.CenterOfMass())
		dirXList = self.inputs['Dir X'].sv_get(deepcopy=True)
		dirYList = self.inputs['Dir Y'].sv_get(deepcopy=True)
		dirZList = self.inputs['Dir Z'].sv_get(deepcopy=True)
		degreeList = self.inputs['Degree'].sv_get(deepcopy=True)
		sidesList = self.inputs['Sides'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		dirXList = Replication.flatten(dirXList)
		dirYList = Replication.flatten(dirYList)
		dirZList = Replication.flatten(dirZList)
		degreeList = Replication.flatten(degreeList)
		sidesList = Replication.flatten(sidesList)
		toleranceList = Replication.flatten(toleranceList)
		inputs = [wireList, originList, dirXList, dirYList, dirZList, degreeList, sidesList, toleranceList]
		if ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = Replication.repeat(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(Replication.interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologySpin)

def unregister():
	bpy.utils.unregister_class(SvTopologySpin)
