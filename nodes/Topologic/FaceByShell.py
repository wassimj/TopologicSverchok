import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import ShellExternalBoundary, WireByVertices, VertexProject, WireRemoveCollinearEdges, Replication

def planarize(wire):
	verts = []
	_ = wire.Vertices(None, verts)
	w = WireByVertices.processItem([[verts[0], verts[1], verts[2]], True])
	f = topologic.Face.ByExternalBoundary(w)
	proj_verts = []
	for v in verts:
		proj_verts.append(VertexProject.processItem([v, f]))
	new_w = WireByVertices.processItem([proj_verts, True])
	return new_w

def planarizeList(wireList):
	returnList = []
	for aWire in wireList:
		returnList.append(planarize(aWire))
	return returnList

def processItem(item):
	shell, angTol = item
	ext_boundary = ShellExternalBoundary.processItem(shell)
	if isinstance(ext_boundary, topologic.Wire):
		try:
			return topologic.Face.ByExternalBoundary(WireRemoveCollinearEdges.processItem([ext_boundary, angTol]))
		except:
			try:
				return topologic.Face.ByExternalBoundary(planarize(WireRemoveCollinearEdges.processItem([ext_boundary, angTol])))
			except:
				print("FaceByPlanarShell - Error: The input Wire is not planar and could not be fixed. Returning the planarized Wire.")
				return planarize(ext_boundary)
	elif isinstance(ext_boundary, topologic.Cluster):
		wires = []
		_ = ext_boundary.Wires(None, wires)
		faces = []
		areas = []
		for aWire in wires:
			try:
				aFace = topologic.Face.ByExternalBoundary(WireRemoveCollinearEdges.processItem([aWire, angTol]))
			except:
				aFace = topologic.Face.ByExternalBoundary(planarize(WireRemoveCollinearEdges.processItem([aWire, angTol])))
			anArea = topologic.FaceUtility.Area(aFace)
			faces.append(aFace)
			areas.append(anArea)
		max_index = areas.index(max(areas))
		ext_boundary = faces[max_index]
		int_boundaries = list(set(faces) - set([ext_boundary]))
		int_wires = []
		for int_boundary in int_boundaries:
			temp_wires = []
			_ = int_boundary.Wires(None, temp_wires)
			int_wires.append(WireRemoveCollinearEdges.processItem([temp_wires[0], angTol]))
		temp_wires = []
		_ = ext_boundary.Wires(None, temp_wires)
		ext_wire = WireRemoveCollinearEdges.processItem([temp_wires[0], angTol])
		try:
			return topologic.Face.ByExternalInternalBoundaries(ext_wire, int_wires)
		except:
			return topologic.Face.ByExternalInternalBoundaries(planarize(ext_wire), planarizeList(int_wires))
	else:
		return None

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvFaceByShell(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face from the input Shell. The Shell must be planar within the input Angular Tolerance
	"""
	bl_idname = 'SvFaceByShell'
	bl_label = 'Face.ByShell'
	bl_icon = 'SELECT_DIFFERENCE'

	AngTol: FloatProperty(name='Angular Tolerance', default=0.1, min=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Shell')
		self.inputs.new('SvStringsSocket', 'Angular Tolerance').prop_name='AngTol'
		self.outputs.new('SvStringsSocket', 'Face')
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
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceByShell)

def unregister():
	bpy.utils.unregister_class(SvFaceByShell)
