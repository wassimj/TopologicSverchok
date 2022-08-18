import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

from . import TopologyClusterFaces, FaceByShell, Replication

def processItem(item):
	topology, angTol, tolerance = item
	t = topology.Type()
	if (t == 1) or (t == 2) or (t == 4) or (t == 8) or (t == 128):
		return topology
	clusters = TopologyClusterFaces.processItem([topology, tolerance])
	faces = []
	for aCluster in clusters:
		shells = []
		_ = aCluster.Shells(None, shells)
		shells = Replication.flatten(shells)
		for aShell in shells:
			aFace = FaceByShell.processItem([aShell, angTol])
			if aFace:
				if isinstance(aFace, topologic.Face):
					faces.append(aFace)
	returnTopology = None
	if t == 16:
		returnTopology = topologic.Shell.ByFaces(faces, tolerance)
		if not returnTopology:
			returnTopology = topologic.Cluster.ByTopologies(faces, False)
	elif t == 32:
		returnTopology = topologic.Cell.ByFaces(faces, tolerance)
		if not returnTopology:
			returnTopology = topologic.Shell.ByFaces(faces, tolerance)
		if not returnTopology:
			returnTopology = topologic.Cluster.ByTopologies(faces, False)
	elif t == 64:
		returnTopology = topologic.CellComplex.ByFaces(faces, tolerance, False)
		if not returnTopology:
			returnTopology = topologic.Cell.ByFaces(faces, tolerance)
		if not returnTopology:
			returnTopology = topologic.Shell.ByFaces(faces, tolerance)
		if not returnTopology:
			returnTopology = topologic.Cluster.ByTopologies(faces, False)
	return returnTopology

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvTopologyRemoveCoplanarFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Removes any coplanar faces from the input Topology    
	"""
	bl_idname = 'SvTopologyRemoveCoplanarFaces'
	bl_label = 'Topology.RemoveCoplanarFaces'
	bl_icon = 'SELECT_DIFFERENCE'

	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	AngTol: FloatProperty(name='Angular Tolerance', default=0.1, min=0, precision=4, update=updateNode)
	Tol: FloatProperty(name='Tolerance', default=0.0001, min=0, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Angular Tolerance').prop_name='AngTol'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Topology')
		self.width = 250
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
		if len(outputs) == 1:
			if isinstance(outputs[0], list):
				outputs = outputs[0]
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvTopologyRemoveCoplanarFaces)

def unregister():
    bpy.utils.unregister_class(SvTopologyRemoveCoplanarFaces)
