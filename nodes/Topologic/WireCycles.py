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





#Based on open source code from: https://stackoverflow.com/questions/12367801/finding-all-cycles-in-undirected-graphs

def vIndex(v, vList, tolerance):
    for i in range(len(vList)):
        if topologic.VertexUtility.Distance(v, vList[i]) < tolerance:
            return i+1
    return None

#  rotate cycle path such that it begins with the smallest node
def rotate_to_smallest(path):
    n = path.index(min(path))
    return path[n:]+path[:n]

def invert(path):
    return rotate_to_smallest(path[::-1])

def isNew(cycles, path):
    return not path in cycles

def visited(node, path):
    return node in path

def findNewCycles(graph, cycles, path, maxVertices):
    if len(path) > maxVertices:
        return
    start_node = path[0]
    next_node= None
    sub = []

    #visit each edge and each node of each edge
    for edge in graph:
        node1, node2 = edge
        if start_node in edge:
                if node1 == start_node:
                    next_node = node2
                else:
                    next_node = node1
                if not visited(next_node, path):
                        # neighbor node not on path yet
                        sub = [next_node]
                        sub.extend(path)
                        # explore extended path
                        findNewCycles(graph, cycles, sub, maxVertices);
                elif len(path) > 2  and next_node == path[-1]:
                        # cycle found
                        p = rotate_to_smallest(path);
                        inv = invert(p)
                        if isNew(cycles, p) and isNew(cycles, inv):
                            cycles.append(p)

def main(graph, cycles, maxVertices):
    returnValue = []
    for edge in graph:
        for node in edge:
            findNewCycles(graph, cycles, [node], maxVertices)
    for cy in cycles:
        row = []
        for node in cy:
            row.append(node)
        returnValue.append(row)
    return returnValue

def processItem(item):
	wire = item[0]
	maxVertices = item[1]
	tolerance = item[2]

	tEdges = []
	_ = wire.Edges(None, tEdges)
	tVertices = []
	_ = wire.Vertices(None, tVertices)
	tVertices = tVertices

	graph = []
	for anEdge in tEdges:
		graph.append([vIndex(anEdge.StartVertex(), tVertices, tolerance), vIndex(anEdge.EndVertex(), tVertices, tolerance)])

	cycles = []
	resultingCycles = main(graph, cycles, maxVertices)

	result = []
	for aRow in resultingCycles:
		row = []
		for anIndex in aRow:
			row.append(tVertices[anIndex-1])
		result.append(row)

	resultWires = []
	for i in range(len(result)):
		c = result[i]
		resultEdges = []
		for j in range(len(c)-1):
			v1 = c[j]
			v2 = c[j+1]
			e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
			resultEdges.append(e)
		e = topologic.Edge.ByStartVertexEndVertex(c[len(c)-1], c[0])
		resultEdges.append(e)
		resultWire = topologic.Wire.ByEdges(resultEdges)
		resultWires.append(resultWire)
	return resultWires

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvWireCycles(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the closed cycles (Wires) with the maximum number of input Vertices found in the input Wire    
	"""
	bl_idname = 'SvWireCycles'
	bl_label = 'Wire.Cycles'
	bl_icon = 'SELECT_DIFFERENCE'
	MaxVertices: IntProperty(name="Max Vertices", default=16, min=3, max=360, update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.inputs.new('SvStringsSocket', 'Max Vertices').prop_name = 'MaxVertices'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Cycles')
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
		self.outputs['Cycles'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvWireCycles)

def unregister():
	bpy.utils.unregister_class(SvWireCycles)
