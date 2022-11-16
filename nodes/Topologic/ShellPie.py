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
from . import Replication

def wireByVertices(vList):
	edges = []
	for i in range(len(vList)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def processItem(item):
    origin, \
    radiusA, \
    radiusB, \
    sides, \
    rings, \
    fromAngle, \
    toAngle, \
    dirX, \
    dirY, \
    dirZ, \
    tolerance, \
    placement = item
    if not origin:
        origin = Vertex.ByCoordinates(0,0,0)
    if not isinstance(origin, topologic.Vertex):
        return None
    if toAngle < fromAngle:
        toAngle += 360
    if abs(toAngle-fromAngle) < tolerance:
        return None
    fromAngle = math.radians(fromAngle)
    toAngle = math.radians(toAngle)
    angleRange = toAngle - fromAngle
    radiusA = abs(radiusA)
    radiusB = abs(radiusB)
    if radiusB > radiusA:
        temp = radiusA
        radiusA = radiusB
        radiusB = temp
    if abs(radiusA - radiusB) < tolerance or radiusA < tolerance:
        return None
    radiusRange = radiusA - radiusB
    print("Radius Range", radiusRange)
    sides = int(abs(math.floor(sides)))
    if sides < 3:
        return None
    rings = int(abs(rings))
    if radiusB < tolerance:
        radiusB = 0
    xOffset = 0
    yOffset = 0
    zOffset = 0
    if placement.lower() == "lowerleft":
        xOffset = radiusA
        yOffset = radiusA
    uOffset = float(angleRange)/float(sides)
    vOffset = float(radiusRange)/float(rings)
    faces = []
    if radiusB > tolerance:
        for i in range(rings):
            r1 = radiusA - vOffset*i
            r2 = radiusA - vOffset*(i+1)
            for j in range(sides):
                a1 = fromAngle + uOffset*j
                a2 = fromAngle + uOffset*(j+1)
                x1 = math.sin(a1)*r1
                y1 = math.cos(a1)*r1
                z1 = 0
                x2 = math.sin(a1)*r2
                y2 = math.cos(a1)*r2
                z2 = 0
                x3 = math.sin(a2)*r2
                y3 = math.cos(a2)*r2
                z3 = 0
                x4 = math.sin(a2)*r1
                y4 = math.cos(a2)*r1
                z4 = 0
                v1 = Vertex.ByCoordinates(x1,y1,z1)
                v2 = Vertex.ByCoordinates(x2,y2,z2)
                v3 = Vertex.ByCoordinates(x3,y3,z3)
                v4 = Vertex.ByCoordinates(x4,y4,z4)
                f1 = Face.ByExternalBoundary(wireByVertices([v1,v2,v3,v4]))
                faces.append(f1)
    else:
        x1 = 0
        y1 = 0
        z1 = 0
        v1 = Vertex.ByCoordinates(x1,y1,z1)
        for j in range(sides):
            a1 = fromAngle + uOffset*j
            a2 = fromAngle + uOffset*(j+1)
            x2 = math.sin(a1)*radiusA
            y2 = math.cos(a1)*radiusA
            z2 = 0
            x3 = math.sin(a2)*radiusA
            y3 = math.cos(a2)*radiusA
            z3 = 0
            v2 = Vertex.ByCoordinates(x2,y2,z2)
            v3 = Vertex.ByCoordinates(x3,y3,z3)
            f1 = Face.ByExternalBoundary(wireByVertices([v2,v1,v3]))
            faces.append(f1)

    shell = Shell.ByFaces(faces, tolerance)
    if not shell:
        return None
    x1 = 0
    y1 = 0
    z1 = 0
    x2 = 0 + dirX
    y2 = 0 + dirY
    z2 = 0 + dirZ
    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1    
    dist = math.sqrt(dx**2 + dy**2 + dz**2)
    phi = math.degrees(math.atan2(dy, dx)) # Rotation around Y-Axis
    if dist < tolerance:
        theta = 0
    else:
        theta = math.degrees(math.acos(dz/dist)) # Rotation around Z-Axis
    shell = topologic.TopologyUtility.Rotate(shell, origin, 0, 1, 0, theta)
    shell = topologic.TopologyUtility.Rotate(shell, origin, 0, 0, 1, phi)
    shell = topologic.TopologyUtility.Translate(shell, origin.X()+xOffset, origin.Y()+yOffset, origin.Z()+zOffset)
    return shell

placements = [("Center", "Center", "", 1),("LowerLeft", "LowerLeft", "", 2)]
replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvShellPie(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Pie Shape (Shell) from the input parameters    
	"""
	bl_idname = 'SvShellPie'
	bl_label = 'Shell.Pie'
	bl_icon = 'SELECT_DIFFERENCE'

	RadiusA: FloatProperty(name="Radius A", default=0.5, min=0.0001, precision=4, update=updateNode)
	RadiusB: FloatProperty(name="Radius B", default=0, min=0, precision=4, update=updateNode)
	Sides: IntProperty(name="Sides", default=32, min=3, update=updateNode)
	Rings: IntProperty(name="Rings", default=0, min=0, update=updateNode)
	FromAngle: FloatProperty(name="From Angle", default=0, min=0, max=360, precision=4, update=updateNode)
	ToAngle: FloatProperty(name="To Angle", default=360, min=0, max=360, precision=4, update=updateNode)
	DirX: FloatProperty(name="Dir X", default=0, precision=4, update=updateNode)
	DirY: FloatProperty(name="Dir Y", default=0, precision=4, update=updateNode)
	DirZ: FloatProperty(name="Dir Z", default=1, precision=4, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)
	Placement: EnumProperty(name="Placement", description="Specify origin placement", default="Center", items=placements, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Radius A').prop_name = 'RadiusA'
		self.inputs.new('SvStringsSocket', 'Radius B').prop_name = 'RadiusB'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'Sides'
		self.inputs.new('SvStringsSocket', 'Rings').prop_name = 'Rings'
		self.inputs.new('SvStringsSocket', 'From').prop_name = 'FromAngle'
		self.inputs.new('SvStringsSocket', 'To').prop_name = 'ToAngle'
		self.inputs.new('SvStringsSocket', 'Dir X').prop_name = 'DirX'
		self.inputs.new('SvStringsSocket', 'Dir Y').prop_name = 'DirY'
		self.inputs.new('SvStringsSocket', 'Dir Z').prop_name = 'DirZ'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Shell')
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
		self.outputs['Shell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvShellPie)

def unregister():
	bpy.utils.unregister_class(SvShellPie)
