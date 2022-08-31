import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time
from . import Replication

def boundingBox(cell):
	vertices = []
	_ = cell.Vertices(None, vertices)
	x = []
	y = []
	z = []
	for aVertex in vertices:
		x.append(aVertex.X())
		y.append(aVertex.Y())
		z.append(aVertex.Z())
	return ([min(x), min(y), min(z), max(x), max(y), max(z)])

def isInside(aperture, face, tolerance):
	vertices = []
	_ = aperture.Vertices(None, vertices)
	for vertex in vertices:
		if topologic.FaceUtility.IsInside(face, vertex, tolerance) == False:
			return False
	return True
	
def processItem(item):
	apertures, face = item
	if not isinstance(apertures, list):
		apertures = [apertures]

	for aperture in apertures:
		cen = aperture.CenterOfMass()
		try:
			params = face.ParametersAtVertex(cen)
			u = params[0]
			v = params[1]
		except:
			u = 0.5
			v = 0.5
		context = topologic.Context.ByTopologyParameters(face, u, v, 0.5)
		_ = topologic.Aperture.ByTopologyContext(aperture, context)
	return face

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvFaceAddFaceAsAperture(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Adds the input Aperture Face as an Aperture to the input Host Face
	"""
	bl_idname = 'SvFaceAddFaceAsAperture'
	bl_label = 'Face.AddFaceAsAperture'
	bl_icon = 'SELECT_DIFFERENCE'

	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Aperture Face')
		self.inputs.new('SvStringsSocket', 'Host Face')
		self.outputs.new('SvStringsSocket', 'Host Face')
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
		if len(outputs) == 1:
			if isinstance(outputs[0], list):
				outputs = outputs[0]
		self.outputs['Host Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceAddFaceAsAperture)

def unregister():
	bpy.utils.unregister_class(SvFaceAddFaceAsAperture)
