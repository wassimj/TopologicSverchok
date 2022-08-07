import bpy
from bpy.props import FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def unitizeVector(vector):
	mag = 0
	for value in vector:
		mag += value ** 2
	mag = mag ** 0.5
	unitVector = []
	for i in range(len(vector)):
		unitVector.append(vector[i] / mag)
	return unitVector

def multiplyVector(vector, mag, tol):
	oldMag = 0
	for value in vector:
		oldMag += value ** 2
	oldMag = oldMag ** 0.5
	if oldMag < tol:
		return [0,0,0]
	newVector = []
	for i in range(len(vector)):
		newVector.append(vector[i] * mag / oldMag)
	return newVector

def processItem(item):
	edge, distance, vertex, tol = item
	if not isinstance(edge, topologic.Edge):
		return None
	if (not vertex) or (vertex == 0):
		vertex = edge.StartVertex()
	rv = None
	sv = edge.StartVertex()
	ev = edge.EndVertex()
	vx = ev.X() - sv.X()
	vy = ev.Y() - sv.Y()
	vz = ev.Z() - sv.Z()
	vector = unitizeVector([vx, vy, vz])
	vector = multiplyVector(vector, distance, tol)
	if vertex == None:
		vertex = sv
	rv = topologic.Vertex.ByCoordinates(vertex.X()+vector[0], vertex.Y()+vector[1], vertex.Z()+vector[2])
	return rv

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvEdgeVertexByDistance(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Vertex at the distance from the start Vertex of the input Edge or an optional Vertex
	"""
	bl_idname = 'SvEdgeVertexByDistance'
	bl_label = 'Edge.VertexByDistance'
	bl_icon = 'SELECT_DIFFERENCE'

	Parameter: FloatProperty(name="Distance", default=1.0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.inputs.new('SvStringsSocket', 'Distance').prop_name='Parameter'
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Vertex')
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
			if anInput.name == 'Origin':
				if not (self.inputs['Origin'].is_linked):
					inp = [[0]]
				else:
					inp = anInput.sv_get(deepcopy=True)
			else:
				inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		inputs_replicated = Replication.replicateInputs(inputs_flat, self.Replication)
		outputs = []
		for anInput in inputs_replicated:
			outputs.append(processItem(anInput))
		inputs_flat = []
		for anInput in self.inputs:
			if anInput.name == 'Origin':
				if not (self.inputs['Origin'].is_linked):
					inp = [[0]]
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
		if len(outputs) == 1:
			if isinstance(outputs[0], list):
				outputs = outputs[0]
		self.outputs['Vertex'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEdgeVertexByDistance)

def unregister():
	bpy.utils.unregister_class(SvEdgeVertexByDistance)
