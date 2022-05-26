import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time

def processItem(item):
	if item.Type() != 128:
		item = topologic.Cluster.ByTopologies([item])
	resultingTopologies = []
	topCC = []
	_ = item.CellComplexes(None, topCC)
	topCells = []
	_ = item.Cells(None, topCells)
	topShells = []
	_ = item.Shells(None, topShells)
	topFaces = []
	_ = item.Faces(None, topFaces)
	topWires = []
	_ = item.Wires(None, topWires)
	topEdges = []
	_ = item.Edges(None, topEdges)
	topVertices = []
	_ = item.Vertices(None, topVertices)
	if len(topCC) == 1:
		cc = topCC[0]
		ccVertices = []
		_ = cc.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(cc)
	if len(topCC) == 0 and len(topCells) == 1:
		cell = topCells[0]
		ccVertices = []
		_ = cell.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(cell)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 1:
		shell = topShells[0]
		ccVertices = []
		_ = shell.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(shell)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 1:
		face = topFaces[0]
		ccVertices = []
		_ = face.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(face)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 1:
		wire = topWires[0]
		ccVertices = []
		_ = wire.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(wire)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 0 and len(topEdges) == 1:
		edge = topEdges[0]
		ccVertices = []
		_ = edge.Vertices(None, ccVertices)
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
