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
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import math
from . import Replication, WireRectangle

def wireByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def sliceCell(cell, width, length, height, uSides, vSides, wSides):
	origin = cell.Centroid()
	shells = []
	_ = cell.Shells(None, shells)
	shell = shells[0]
	wRect = WireRectangle.processItem([origin, width*1.2, length*1.2, 0, 0, 1, "Center"])
	sliceFaces = []
	for i in range(1, wSides):
		sliceFaces.append(topologic.TopologyUtility.Translate(topologic.Face.ByExternalBoundary(wRect), 0, 0, height/wSides*i - height*0.5))
	uRect = WireRectangle.processItem([origin, height*1.2, length*1.2, 1, 0, 0, "Center"])
	for i in range(1, uSides):
		sliceFaces.append(topologic.TopologyUtility.Translate(topologic.Face.ByExternalBoundary(uRect), width/uSides*i - width*0.5, 0, 0))
	vRect = WireRectangle.processItem([origin, height*1.2, width*1.2, 0, 1, 0, "Center"])
	for i in range(1, vSides):
		sliceFaces.append(topologic.TopologyUtility.Translate(topologic.Face.ByExternalBoundary(vRect), 0, length/vSides*i - length*0.5, 0))
	sliceCluster = topologic.Cluster.ByTopologies(sliceFaces)
	shell = shell.Slice(sliceCluster, False)
	return topologic.Cell.ByShell(shell)

def processItem(item):
	origin, \
	width, \
	length, \
	height, \
	uSides, \
	vSides, \
	wSides, \
	dirX, \
	dirY, \
	dirZ, \
    placement = item
	xOffset = 0
	yOffset = 0
	zOffset = 0
	if placement == "Center":
		zOffset = -height*0.5
	elif placement == "LowerLeft":
		xOffset = width*0.5
		yOffset = length*0.5

	vb1 = topologic.Vertex.ByCoordinates(origin.X()-width*0.5+xOffset,origin.Y()-length*0.5+yOffset,origin.Z()+zOffset)
	vb2 = topologic.Vertex.ByCoordinates(origin.X()+width*0.5+xOffset,origin.Y()-length*0.5+yOffset,origin.Z()+zOffset)
	vb3 = topologic.Vertex.ByCoordinates(origin.X()+width*0.5+xOffset,origin.Y()+length*0.5+yOffset,origin.Z()+zOffset)
	vb4 = topologic.Vertex.ByCoordinates(origin.X()-width*0.5+xOffset,origin.Y()+length*0.5+yOffset,origin.Z()+zOffset)

	vt1 = topologic.Vertex.ByCoordinates(origin.X()-width*0.5+xOffset,origin.Y()-length*0.5+yOffset,origin.Z()+height+zOffset)
	vt2 = topologic.Vertex.ByCoordinates(origin.X()+width*0.5+xOffset,origin.Y()-length*0.5+yOffset,origin.Z()+height+zOffset)
	vt3 = topologic.Vertex.ByCoordinates(origin.X()+width*0.5+xOffset,origin.Y()+length*0.5+yOffset,origin.Z()+height+zOffset)
	vt4 = topologic.Vertex.ByCoordinates(origin.X()-width*0.5+xOffset,origin.Y()+length*0.5+yOffset,origin.Z()+height+zOffset)
	baseWire = wireByVertices([vb1, vb2, vb3, vb4])
	topWire = wireByVertices([vt1, vt2, vt3, vt4])
	wires = [baseWire, topWire]
	prism =  topologic.CellUtility.ByLoft(wires)
	prism = sliceCell(prism, width, length, height, uSides, vSides, wSides)
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
	prism = topologic.TopologyUtility.Rotate(prism, origin, 0, 1, 0, theta)
	prism = topologic.TopologyUtility.Rotate(prism, origin, 0, 0, 1, phi)
	return prism

placements = [("Bottom", "Bottom", "", 1),("Center", "Center", "", 2),("LowerLeft", "Lower Left", "", 3)]
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvCellPrism(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Prism (Cell) from the input cuboid parameters    
	"""
	bl_idname = 'SvCellPrism'
	bl_label = 'Cell.Prism'
	bl_icon = 'SELECT_DIFFERENCE'
	Width: FloatProperty(name="Width", default=1, min=0.0001, precision=4, update=updateNode)
	Length: FloatProperty(name="Length", default=1, min=0.0001, precision=4, update=updateNode)
	Height: FloatProperty(name="Height", default=1, min=0.0001, precision=4, update=updateNode)
	USides: IntProperty(name="U Sides", default=1, min=1, update=updateNode)
	VSides: IntProperty(name="V Sides", default=1, min=1, update=updateNode)
	WSides: IntProperty(name="W Sides", default=1, min=1, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)

	Placement: EnumProperty(name="Placement", description="Placement", default="Bottom", items=placements, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.width = 150
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Width').prop_name = 'Width'
		self.inputs.new('SvStringsSocket', 'Length').prop_name = 'Length'
		self.inputs.new('SvStringsSocket', 'Height').prop_name = 'Height'
		self.inputs.new('SvStringsSocket', 'U Sides').prop_name = 'USides'
		self.inputs.new('SvStringsSocket', 'V Sides').prop_name = 'VSides'
		self.inputs.new('SvStringsSocket', 'W Sides').prop_name = 'WSides'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.outputs.new('SvStringsSocket', 'Cell')
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
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		if self.Replication == "Interlace":
			outputs = Replication.re_interlace(outputs, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			outputs = Replication.unflatten(outputs, match_list)
		if len(outputs) == 1:
			if isinstance(outputs[0], list):
				outputs = outputs[0]
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellPrism)

def unregister():
	bpy.utils.unregister_class(SvCellPrism)
