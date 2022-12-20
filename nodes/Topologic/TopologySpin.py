import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from . import Replication, ShellByLoft, CellComplexByLoft, TopologySelfMerge, WireByVertices, TopologyRotate

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
		topologies.append(TopologyRotate.processItem([topology, origin, dirX, dirY, dirZ, unit_degree*i]))
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

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvTopologySpin(SverchCustomTreeNode, bpy.types.Node):
	"""
	Triggers: Topologic
	Tooltip: Spins the input Wire based on the input number of sides, rotation origin, axis of rotation, and degrees    
	"""
	bl_idname = 'SvTopologySpin'
	bl_label = 'Topology.Spin'
	bl_icon = 'SELECT_DIFFERENCE'
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y",  default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z",  default=1, precision=4, update=updateNode)
	Degree: FloatProperty(name="Degree",  default=0, precision=4, update=updateNode)
	Sides: IntProperty(name="Sides", default=16, min=1, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.width = 175
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.inputs.new('SvStringsSocket', 'Degree').prop_name = 'Degree'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'Sides'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Topology')
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Replication")
		split.row().prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return

		inputs_nested = []
		inputs_flat = []
		for anInput in self.inputs:
			if anInput == self.inputs['Origin']:
				if not anInput.is_linked:
					inp = topologic.Vertex.ByCoordinates(0,0,0)
				else:
					inp = anInput.sv_get(deepcopy=True)
			else:
				inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		inputs_replicated = Replication.replicateInputs(inputs_flat.copy(), self.Replication)
		outputs = []
		for anInput in inputs_replicated:
			outputs.append(processItem(anInput))
		inputs_flat = []
		for anInput in self.inputs:
			if anInput == self.inputs['Origin']:
				if not anInput.is_linked:
					inp = topologic.Vertex.ByCoordinates(0,0,0)
				else:
					inp = anInput.sv_get(deepcopy=True)
			else:
				inp = anInput.sv_get(deepcopy=True)
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			outputs = Replication.re_interlace(outputs, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			outputs = Replication.unflatten(outputs, match_list)
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologySpin)

def unregister():
	bpy.utils.unregister_class(SvTopologySpin)
