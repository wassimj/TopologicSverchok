import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from . import Replication
from . import TopologyTranslate

def processItem(item):
	topology, oldLoc, clusterLoc = item
	returnTopologies = []
	if not isinstance(clusterLoc, topologic.Cluster):
		clusterLoc = topologic.Cluster.ByTopologies([clusterLoc])
	newLocations = []
	clusterLoc.Vertices(None, newLocations)
	for newLoc in newLocations:
		x = newLoc.X() - oldLoc.X()
		y = newLoc.Y() - oldLoc.Y()
		z = newLoc.Z() - oldLoc.Z()
		newTopology = None
		try:
			newTopology = TopologyTranslate.processItem([topology, x, y, z])
		except:
			print("ERROR: (Topologic>TopologyUtility.Place) operation failed.")
			newTopology = None
		if newTopology:
			returnTopologies.append(newTopology)
	if len(returnTopologies) > 1:
		returnTopology = topologic.Cluster.ByTopologies(returnTopologies)
	elif len(returnTopologies) == 1:
		returnTopology = returnTopologies[0]
	else:
		returnTopology = None
	return returnTopology

replication = [("Default", "Default", "", 1), ("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
		
class SvTopologyPlace(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Places the input Topology at the new input location    
	"""
	bl_idname = 'SvTopologyPlace'
	bl_label = 'Topology.Place'
	bl_icon = 'SELECT_DIFFERENCE'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Old Location')
		self.inputs.new('SvStringsSocket', 'New Location')
		self.outputs.new('SvStringsSocket', 'Topology')
		self.width = 200
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
		inputs_nested = []
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		inputs_replicated = Replication.replicateInputs(inputs_flat, self.Replication)
		outputs = []
		for anInput in inputs_replicated:
			outputs.append(processItem(anInput))
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			outputs = Replication.re_interlace(outputs, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			outputs = Replication.unflatten(outputs, match_list)
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyPlace)

def unregister():
	bpy.utils.unregister_class(SvTopologyPlace)
