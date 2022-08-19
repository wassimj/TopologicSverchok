# * This file is part of Topologic software library.
# * Copyright(C) 2021, Cardiff University and University College London
# * 
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU Affero General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# * 
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU Affero General Public License for more details.
# * 
# * You should have received a copy of the GNU Affero General Public License
# * along with this program. If not, see <https://www.gnu.org/licenses/>.

import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from . import Replication, WireByVertices
import math

def wireByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def processItem(item, originLocation, inputMode):
	if inputMode == "Width and Length":
		origin, w, l, sides, fromAngle, toAngle, close, dirX, dirY, dirZ = item
		a = w/2
		b = l/2
		c = math.sqrt(abs(b**2 - a**2))
		e = c/a
	elif inputMode == "Focal Length and Eccentricity":
		origin, c, e, sides, fromAngle, toAngle, close, dirX, dirY, dirZ = item
		a = c/e
		b = math.sqrt(abs(a**2 - c**2))
		w = a*2
		l = b*2
	elif inputMode == "Focal Length and Minor Axis":
		origin, c, b, sides, fromAngle, toAngle, close, dirX, dirY, dirZ = item
		a = math.sqrt(abs(b**2 + c**2))
		e = c/a
		w = a*2
		l = b*2
	elif inputMode == "Major Axis Length and Minor Axis Length":
		origin, a, b, sides, fromAngle, toAngle, close, dirX, dirY, dirZ = item
		c = math.sqrt(abs(b**2 - a**2))
		e = c/a
		w = a*2
		l = b*2
	else:
		raise NotImplementedError
	baseV = []
	xList = []
	yList = []

	if toAngle < fromAngle:
		toAngle += 360
	elif toAngle == fromAngle:
		raise Exception("Wire.Ellipse - Error: To angle cannot be equal to the From Angle")

	angleRange = toAngle - fromAngle
	fromAngle = math.radians(fromAngle)
	toAngle = math.radians(toAngle)
	sides = int(math.floor(sides))
	for i in range(sides+1):
		angle = fromAngle + math.radians(angleRange/sides)*i
		x = math.sin(angle)*a + origin.X()
		y = math.cos(angle)*b + origin.Y()
		z = origin.Z()
		xList.append(x)
		yList.append(y)
		baseV.append(topologic.Vertex.ByCoordinates(x,y,z))

	ellipse = WireByVertices.processItem([baseV[::-1], close]) #reversing the list so that the normal points up in Blender

	if originLocation == "LowerLeft":
		xmin = min(xList)
		ymin = min(yList)
		ellipse = topologic.TopologyUtility.Translate(ellipse, a, b, 0)
	x1 = origin.X()
	y1 = origin.Y()
	z1 = origin.Z()
	x2 = origin.X() + dirX
	y2 = origin.Y() + dirY
	z2 = origin.Z() + dirZ
	dx = x2 - x1
	dy = y2 - y1
	dz = z2 - z1    
	dist = math.sqrt(dx**2 + dy**2 + dz**2)
	phi = math.degrees(math.atan2(dy, dx)) # Rotation around Y-Axis
	if dist < 0.0001:
		theta = 0
	else:
		theta = math.degrees(math.acos(dz/dist)) # Rotation around Z-Axis
	ellipse = topologic.TopologyUtility.Rotate(ellipse, origin, 0, 1, 0, theta)
	ellipse = topologic.TopologyUtility.Rotate(ellipse, origin, 0, 0, 1, phi)

	# Create a Cluster of the two foci
	v1 = topologic.Vertex.ByCoordinates(c+origin.X(), 0+origin.Y(),0)
	v2 = topologic.Vertex.ByCoordinates(-c+origin.X(), 0+origin.Y(),0)
	foci = topologic.Cluster.ByTopologies([v1, v2])
	if originLocation == "LowerLeft":
		foci = topologic.TopologyUtility.Translate(foci, a, b, 0)
	foci = topologic.TopologyUtility.Rotate(foci, origin, 0, 1, 0, theta)
	foci = topologic.TopologyUtility.Rotate(foci, origin, 0, 0, 1, phi)
	return [ellipse, foci, a, b, c, e, w, l]

def update_sockets(self, context):
	# hide all input sockets
	self.inputs['Width'].hide_safe = True
	self.inputs['Length'].hide_safe = True
	self.inputs['Focal Length'].hide_safe = True
	self.inputs['Eccentricity'].hide_safe = True
	self.inputs['Major Axis Length'].hide_safe = True
	self.inputs['Minor Axis Length'].hide_safe = True
	if self.InputMode == "Width and Length":
		self.inputs['Width'].hide_safe = False
		self.inputs['Length'].hide_safe = False
	if self.InputMode == "Focal Length and Eccentricity":
		self.inputs['Focal Length'].hide_safe = False
		self.inputs['Eccentricity'].hide_safe = False
	elif self.InputMode == "Focal Length and Minor Axis":
		self.inputs['Focal Length'].hide_safe = False
		self.inputs['Minor Axis Length'].hide_safe = False
	elif self.InputMode == "Major Axis and Minor Axis":
		self.inputs['Major Axis Length'].hide_safe = False
		self.inputs['Minor Axis Length'].hide_safe = False
	updateNode(self, context)

input_items = [("Width and Length", "Width and Length", "", 1),("Focal Length and Eccentricity", "Focal Length and Eccentricity", "", 2),("Focal Length and Minor Axis", "Focal Length and Minor Axis", "", 3), ("Major Axis and Minor Axis", "Major Axis and Minor Axis", "", 4)]
originLocations = [("Center", "Center", "", 1),("LowerLeft", "LowerLeft", "", 2)]
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvWireEllipse(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates an Ellipse (Wire) from the input parameters    
	"""
	bl_idname = 'SvWireEllipse'
	bl_label = 'Wire.Ellipse'
	bl_icon = 'SELECT_DIFFERENCE'

	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	FocalLengthProp: FloatProperty(name="Focal Length", description="The focal length is the distance from the center of the ellipse to one of the two foci", default=0.866025, min=0.0001, precision=6, update=updateNode)
	EccentricityProp: FloatProperty(name="Eccentricity", description="Eccentricity is The ratio of distances from the center of the ellipse from either focus to the semi-major axis of the ellipse (e = c/a)", default=0.866025, min=0.0001, max=0.9999, precision=6, update=updateNode)
	MajorAxisLengthProp: FloatProperty(name="Major Axis Length", description="The length of the major axis of the ellipse", default=1, min=0.0001, precision=4, update=updateNode)
	MinorAxisLengthProp: FloatProperty(name="Minor Axis Length", description="The length of the minor axis of the ellipse", default=0.5, min=0.0001, precision=4, update=updateNode)
	WidthProp: FloatProperty(name="Width", description="The width of the ellipse", default=2, min=0.0001, precision=4, update=updateNode)
	LengthProp: FloatProperty(name="Length", description="The length of the ellipse", default=1, min=0.0001, precision=4, update=updateNode)
	FromProp: FloatProperty(name="From", description="The start angle of the ellipse", default=0, min=0, max=360, precision=4, update=updateNode)
	ToProp: FloatProperty(name="To", description="The end angle of the ellipse", default=360, min=0, max=360, precision=4, update=updateNode)
	SidesProp: IntProperty(name="Sides", default=32, min=4, update=updateNode)
	CloseProp: BoolProperty(name="Close", description="Do you wish to close the returned Wire?", default=True, update=updateNode)
	DirXProp: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirYProp: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZProp: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	Placement: EnumProperty(name="Placement", description="Specify origin placement", default="Center", items=originLocations, update=updateNode)
	InputMode : EnumProperty(name='Input Mode', description='The input component format of the data', items=input_items, default="Width and Length", update=update_sockets)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Focal Length').prop_name = 'FocalLengthProp'
		self.inputs.new('SvStringsSocket', 'Eccentricity').prop_name = 'EccentricityProp'
		self.inputs.new('SvStringsSocket', 'Major Axis Length').prop_name = 'MajorAxisLengthProp'
		self.inputs.new('SvStringsSocket', 'Minor Axis Length').prop_name = 'MinorAxisLengthProp'
		self.inputs.new('SvStringsSocket', 'Width').prop_name = 'WidthProp'
		self.inputs.new('SvStringsSocket', 'Length').prop_name = 'LengthProp'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'SidesProp'
		self.inputs.new('SvStringsSocket', 'From').prop_name = 'FromProp'
		self.inputs.new('SvStringsSocket', 'To').prop_name = 'ToProp'
		self.inputs.new('SvStringsSocket', 'Close').prop_name = 'CloseProp'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirXProp'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirYProp'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZProp'
		self.outputs.new('SvStringsSocket', 'Ellipse')
		self.outputs.new('SvStringsSocket', 'Foci')
		self.outputs.new('SvStringsSocket', 'Focal Length')
		self.outputs.new('SvStringsSocket', 'Eccentricity')
		self.outputs.new('SvStringsSocket', 'Major Axis Length')
		self.outputs.new('SvStringsSocket', 'Minor Axis Length')
		self.outputs.new('SvStringsSocket', 'Width')
		self.outputs.new('SvStringsSocket', 'Length')
		update_sockets(self, context)
		self.width = 325
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.35)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.35)
		split.row().label(text="Replication")
		split.row().prop(self, "Replication",text="")
		row = layout.row()
		split = row.split(factor=0.35)
		split.row().label(text="Input Mode")
		split.row().prop(self, "InputMode",text="")
		row = layout.row()
		split = row.split(factor=0.35)
		split.row().label(text="Placement")
		split.row().prop(self, "Placement",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		sockets = [self.inputs['Origin']]
		if self.InputMode == "Width and Length":
			sockets.append(self.inputs['Width'])
			sockets.append(self.inputs['Length'])
		elif self.InputMode == "Focal Length and Eccentricity":
			sockets.append(self.inputs['Focal Length'])
			sockets.append(self.inputs['Eccentricity'])
		elif self.InputMode == "Focal Length and Minor Axis":
			sockets.append(self.inputs['Focal Length'])
			sockets.append(self.inputs['Minor Axis Length'])
		elif self.InputMode == "Major Axis and Minor Axis":
			sockets.append(self.inputs['Major Axis Length'])
			sockets.append(self.inputs['Minor Axis Length'])
		sockets.append(self.inputs['Sides'])
		sockets.append(self.inputs['From'])
		sockets.append(self.inputs['To'])
		sockets.append(self.inputs['Close'])
		sockets.append(self.inputs['Dir X'])
		sockets.append(self.inputs['Dir Y'])
		sockets.append(self.inputs['Dir Z'])
		inputs_nested = []
		inputs_flat = []
		for anInput in sockets:
			if anInput.name == 'Origin':
				if not (self.inputs['Origin'].is_linked):
					inp = [topologic.Vertex.ByCoordinates(0,0,0)]
				else:
					inp = anInput.sv_get(deepcopy=True)
			else:
				inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		inputs_replicated = Replication.replicateInputs(inputs_flat, self.Replication)
		ellipseList = []
		fociList = []
		aList = []
		bList = []
		cList = []
		eList = []
		wList = []
		lList = []
		for anInput in inputs_replicated:
			ellipse, foci, a, b, c, e, w, l = processItem(anInput, self.Placement, self.InputMode)
			ellipseList.append(ellipse)
			fociList.append(foci)
			aList.append(a)
			bList.append(b)
			cList.append(c)
			eList.append(e)
			wList.append(w)
			lList.append(l)
		inputs_flat = []
		for anInput in sockets:
			if anInput.name == 'Origin':
				if not (self.inputs['Origin'].is_linked):
					inp = [topologic.Vertex.ByCoordinates(0,0,0)]
				else:
					inp = anInput.sv_get(deepcopy=True)
			else:
				inp = anInput.sv_get(deepcopy=True)
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			ellipseList = Replication.re_interlace(ellipseList, inputs_flat)
			fociList = Replication.re_interlace(fociList, inputs_flat)
			aList = Replication.re_interlace(aList, inputs_flat)
			bList = Replication.re_interlace(bList, inputs_flat)
			cList = Replication.re_interlace(cList, inputs_flat)
			eList = Replication.re_interlace(eList, inputs_flat)
			wList = Replication.re_interlace(wList, inputs_flat)
			lList = Replication.re_interlace(lList, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			ellipseList = Replication.unflatten(ellipseList, match_list)
			fociList = Replication.unflatten(fociList, match_list)
			aList = Replication.unflatten(aList, match_list)
			bList = Replication.unflatten(bList, match_list)
			cList = Replication.unflatten(cList, match_list)
			eList = Replication.unflatten(eList, match_list)
			wList = Replication.unflatten(wList, match_list)
			lList = Replication.unflatten(lList, match_list)
		if len(ellipseList) == 1:
			if isinstance(ellipseList[0], list):
				ellipseList = ellipseList[0]
		if len(fociList) == 1:
			if isinstance(fociList[0], list):
				fociList = fociList[0]
		if len(aList) == 1:
			if isinstance(aList[0], list):
				aList = aList[0]
		if len(bList) == 1:
			if isinstance(bList[0], list):
				bList = bList[0]
		if len(cList) == 1:
			if isinstance(cList[0], list):
				cList = cList[0]
		if len(eList) == 1:
			if isinstance(eList[0], list):
				eList = eList[0]
		if len(wList) == 1:
			if isinstance(wList[0], list):
				wList = wList[0]
		if len(lList) == 1:
			if isinstance(lList[0], list):
				lList = lList[0]
		self.outputs['Ellipse'].sv_set(ellipseList)
		self.outputs['Foci'].sv_set(fociList)
		self.outputs['Major Axis Length'].sv_set(aList)
		self.outputs['Minor Axis Length'].sv_set(bList)
		self.outputs['Focal Length'].sv_set(cList)
		self.outputs['Eccentricity'].sv_set(eList)
		self.outputs['Width'].sv_set(wList)
		self.outputs['Length'].sv_set(lList)

def register():
	bpy.utils.register_class(SvWireEllipse)

def unregister():
	bpy.utils.unregister_class(SvWireEllipse)
