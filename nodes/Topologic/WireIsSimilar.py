import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time
import math
import itertools

from . import Replication

# Python program to find if two lists are cyclically equivalent
# for example [1,2,3,4] is cyclically equivalent to [3,4,1,2]
# Adapted from https://stackoverflow.com/questions/31000591/check-if-a-list-is-a-rotation-of-another-list-that-works-with-duplicates

def isCyclicallyEquivalent(u, v, lengthTolerance, angleTolerance):
	n, i, j = len(u), 0, 0
	if n != len(v):
		return False
	while i < n and j < n:
		if (i % 2) == 0:
			tol = lengthTolerance
		else:
			tol = angleTolerance
		k = 1
		while k <= n and math.fabs(u[(i + k) % n]- v[(j + k) % n]) <= tol:
			k += 1
		if k > n:
			return True
		if math.fabs(u[(i + k) % n]- v[(j + k) % n]) > tol:
			i += k
		else:
			j += k
	return False

def angleBetweenEdges(e1, e2, tolerance):
	a = e1.EndVertex().X() - e1.StartVertex().X()
	b = e1.EndVertex().Y() - e1.StartVertex().Y()
	c = e1.EndVertex().Z() - e1.StartVertex().Z()
	d = topologic.VertexUtility.Distance(e1.EndVertex(), e2.StartVertex())
	if d <= tolerance:
		d = e2.StartVertex().X() - e2.EndVertex().X()
		e = e2.StartVertex().Y() - e2.EndVertex().Y()
		f = e2.StartVertex().Z() - e2.EndVertex().Z()
	else:
		d = e2.EndVertex().X() - e2.StartVertex().X()
		e = e2.EndVertex().Y() - e2.StartVertex().Y()
		f = e2.EndVertex().Z() - e2.StartVertex().Z()
	dotProduct = a*d + b*e + c*f
	modOfVector1 = math.sqrt( a*a + b*b + c*c)*math.sqrt(d*d + e*e + f*f) 
	angle = dotProduct/modOfVector1
	angleInDegrees = math.degrees(math.acos(angle))
	return angleInDegrees

def getInteriorAngles(edges, tolerance):
	angles = []
	for i in range(len(edges)-1):
		e1 = edges[i]
		e2 = edges[i+1]
		angles.append(angleBetweenEdges(e1, e2, tolerance))
	return angles

def getRep(edges, tolerance):
	angles = getInteriorAngles(edges, tolerance)
	lengths = []
	for anEdge in edges:
		lengths.append(topologic.EdgeUtility.Length(anEdge))
	minLength = min(lengths)
	normalisedLengths = []
	for aLength in lengths:
		normalisedLengths.append(aLength/minLength)
	return [x for x in itertools.chain(*itertools.zip_longest(normalisedLengths, angles)) if x is not None]

def processItem(item):
	wireA = item[0]
	wireB = item[1]
	if (wireA.IsClosed() == False):
		raise Exception("Error: Wire.IsSimilar - Wire A is not closed.")
	if (wireB.IsClosed() == False):
		raise Exception("Error: Wire.IsSimilar - Wire B is not closed.")
	edgesA = []
	_ = wireA.Edges(None, edgesA)
	edgesB = []
	_ = wireB.Edges(None, edgesB)
	if len(edgesA) != len(edgesB):
		return False
	lengthTolerance = item[2]
	angleTolerance = item[3]
	repA = getRep(list(edgesA), lengthTolerance)
	repB = getRep(list(edgesB), lengthTolerance)
	if isCyclicallyEquivalent(repA, repB, lengthTolerance, angleTolerance):
		return True
	if isCyclicallyEquivalent(repA, repB[::-1], lengthTolerance, angleTolerance):
		return True
	return False

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvWireIsSimilar(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the input Wires are similar. Outputs False otherwise   
	"""
	bl_idname = 'SvWireIsSimilar'
	bl_label = 'Wire.IsSimilar'
	bl_icon = 'SELECT_DIFFERENCE'

	LengthTolerance: FloatProperty(name="Length Tolerance",  default=0.001, precision=4, update=updateNode)
	AngleTolerance: FloatProperty(name="Angle Tolerance",  default=0.1, precision=2, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire A')
		self.inputs.new('SvStringsSocket', 'Wire B')
		self.inputs.new('SvStringsSocket', 'Length Tolerance').prop_name = 'LengthTolerance'
		self.inputs.new('SvStringsSocket', 'Angle Tolerance').prop_name = 'AngleTolerance'
		self.outputs.new('SvStringsSocket', 'Status')
		self.width = 225
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
		self.outputs['Status'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvWireIsSimilar)

def unregister():
	bpy.utils.unregister_class(SvWireIsSimilar)
