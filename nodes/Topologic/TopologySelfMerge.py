import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy
import time

def processItem(item):
	resultingTopologies = []
	topCC = cppyy.gbl.std.list[topologic.CellComplex.Ptr]()
	_ = item.CellComplexes(topCC)
	topCC = list(topCC)
	topCells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
	_ = item.Cells(topCells)
	topCells = list(topCells)
	topShells = cppyy.gbl.std.list[topologic.Shell.Ptr]()
	_ = item.Shells(topShells)
	topShells = list(topShells)
	topFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	_ = item.Faces(topFaces)
	topFaces = list(topFaces)
	topWires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	_ = item.Wires(topWires)
	topWires = list(topWires)
	topEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	_ = item.Edges(topEdges)
	topEdges = list(topEdges)
	topVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	_ = item.Vertices(topVertices)
	topVertices = list(topVertices)
	if len(topCC) == 1:
		cc = topCC[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = cc.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(cc)
	if len(topCC) == 0 and len(topCells) == 1:
		cell = topCells[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = cell.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(cell)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 1:
		shell = topShells[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = shell.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(shell)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 1:
		face = topFaces[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = face.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(face)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 1:
		wire = topWires[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = wire.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(wire)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 0 and len(topEdges) == 1:
		edge = topEdges[0]
		ccVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = wire.Vertices(ccVertices)
		ccVertices = list(ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(edge)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 0 and len(topEdges) == 0 and len(topVertices) == 1:
		vertex = topVertices[0]
		resultingTopologies.append(vertex)
	if len(resultingTopologies) == 1:
		return resultingTopologies[0]
	return item.SelfMerge()

class SvTopologySelfMerge(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Self-merges the input Topology
	"""
	bl_idname = 'SvTopologySelfMerge'
	bl_label = 'Topology.SelfMerge'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)
		end = time.time()
		print("Topology.Geometry Operation consumed "+str(round(end - start,2))+" seconds")

def register():
	bpy.utils.register_class(SvTopologySelfMerge)

def unregister():
	bpy.utils.unregister_class(SvTopologySelfMerge)
