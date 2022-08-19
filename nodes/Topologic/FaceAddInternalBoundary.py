import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def isInside(ib, face, tolerance):
	vertices = []
	_ = ib.Vertices(None, vertices)
	for vertex in vertices:
		if topologic.FaceUtility.IsInside(face, vertex, tolerance) == False:
			return False
	return True

def processItem(item):
	face, cluster = item
	assert isinstance(face, topologic.Face), "FaceAddInternalBoundaries - Error: The host face input is not a Face"
	assert isinstance(face, topologic.Cluster), "FaceAddInternalBoundaries - Error: The internal boundaries input is not a Cluster"
	wires = []
	_ = cluster.Wires(None, wires)
	faceeb = face.ExternalBoundary()
	faceibList = []
	_ = face.InternalBoundaries(faceibList)
	for wire in wires:
		faceibList.append(wire)
	return topologic.Face.ByExternalInternalBoundaries(faceeb, faceibList)

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvFaceAddInternalBoundaries(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Adds the input internal boundaries (Cluster) to the input Face
	"""
	bl_idname = 'SvFaceAddInternalBoundary'
	bl_label = 'Face.AddInternalBoundary'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'Wires Cluster')
		self.outputs.new('SvStringsSocket', 'Face')
		self.width = 175
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
	bpy.utils.register_class(SvFaceAddInternalBoundaries)

def unregister():
	bpy.utils.unregister_class(SvFaceAddInternalBoundaries)
