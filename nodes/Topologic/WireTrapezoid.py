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
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import math
from . import Replication

def wireByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def processItem(item):
	origin, widthA, widthB, offsetA, offsetB, length, dirX, dirY, dirZ, placement = item

	baseV = []
	xOffset = 0
	yOffset = 0
	if placement == "Center":
		xOffset = -((-widthA*0.5 + offsetA) + (-widthB*0.5 + offsetB) + (widthA*0.5 + offsetA) + (widthB*0.5 + offsetB))/4.0
		print("X OFFSET", xOffset)
		yOffset = 0
	elif placement == "LowerLeft":
		xOffset = -(min((-widthA*0.5 + offsetA), (-widthB*0.5 + offsetB)))
		yOffset = length*0.5

	vb1 = topologic.Vertex.ByCoordinates(origin.X()-widthA*0.5+offsetA+xOffset,origin.Y()-length*0.5+yOffset,origin.Z())
	vb2 = topologic.Vertex.ByCoordinates(origin.X()+widthA*0.5+offsetA+xOffset,origin.Y()-length*0.5+yOffset,origin.Z())
	vb3 = topologic.Vertex.ByCoordinates(origin.X()+widthB*0.5+offsetB+xOffset,origin.Y()+length*0.5+yOffset,origin.Z())
	vb4 = topologic.Vertex.ByCoordinates(origin.X()-widthB*0.5++offsetB+xOffset,origin.Y()+length*0.5+yOffset,origin.Z())

	baseWire = wireByVertices([vb1, vb2, vb3, vb4])
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
	baseWire = topologic.TopologyUtility.Rotate(baseWire, origin, 0, 1, 0, theta)
	baseWire = topologic.TopologyUtility.Rotate(baseWire, origin, 0, 0, 1, phi)
	return baseWire

placements = [("Center", "Center", "", 1),("LowerLeft", "LowerLeft", "", 2)]
replication = [("Default", "Default", "", 1), ("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvWireTrapezoid(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Trapezoid (Wire) from the input parameters    
	"""
	bl_idname = 'SvWireTrapezoid'
	bl_label = 'Wire.Trapezoid'
	bl_icon = 'SELECT_DIFFERENCE'

	WidthA: FloatProperty(name="Width A", default=1, min=0.0001, precision=4, update=updateNode)
	WidthB: FloatProperty(name="Width B", default=0.75, min=0.0001, precision=4, update=updateNode)
	OffsetA: FloatProperty(name="Offset A", default=0, precision=4, update=updateNode)
	OffsetB: FloatProperty(name="Offset B", default=0, precision=4, update=updateNode)
	Length: FloatProperty(name="Length", default=1, min=0.0001, precision=4, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Placement: EnumProperty(name="Placement", description="Specify origin placement", default="Center", items=placements, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Width A').prop_name = 'WidthA'
		self.inputs.new('SvStringsSocket', 'Width B').prop_name = 'WidthB'
		self.inputs.new('SvStringsSocket', 'Offset A').prop_name = 'OffsetA'
		self.inputs.new('SvStringsSocket', 'Offset B').prop_name = 'OffsetB'
		self.inputs.new('SvStringsSocket', 'Length').prop_name = 'Length'

		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.outputs.new('SvStringsSocket', 'Wire')
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
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Placement")
		split.row().prop(self, "Placement",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs_nested = []
		inputs_flat = []
		for anInput in self.inputs:
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
		outputs = []
		for anInput in inputs_replicated:
			outputs.append(processItem(anInput+[self.Placement]))
		inputs_flat = []
		for anInput in self.inputs:
			if anInput.name == 'Origin':
				if not (self.inputs['Origin'].is_linked):
					inp = [topologic.Vertex.ByCoordinates(0,0,0)]
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
		self.outputs['Wire'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvWireTrapezoid)

def unregister():
	bpy.utils.unregister_class(SvWireTrapezoid)
