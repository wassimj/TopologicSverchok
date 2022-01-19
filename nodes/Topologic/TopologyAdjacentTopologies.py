import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic


def processItem(item, hostTopology, topologyType):
	adjacentTopologies = []
	error = False
	itemType = item.Type()
	if itemType == topologic.Vertex.Type():
		if topologyType == "Vertex":
			try:
				_ = item.AdjacentVertices(hostTopology, adjacentTopologies)
			except:
				try:
					_ = item.Vertices(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Edge":
			try:
				_ = topologic.VertexUtility.AdjacentEdges(item, hostTopology, adjacentTopologies)
			except:
				try:
					_ = item.Edges(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Wire":
			try:
				_ = topologic.VertexUtility.AdjacentWires(item, hostTopology, adjacentTopologies)
			except:
				try:
					_ = item.Wires(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Face":
			try:
				_ = topologic.VertexUtility.AdjacentFaces(item, hostTopology, adjacentTopologies)
			except:
				try:
					_ = item.Faces(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Shell":
			try:
				_ = topologic.VertexUtility.AdjacentShells(item, hostTopology, adjacentTopologies)
			except:
				try:
					_ = item.Shells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Cell":
			try:
				_ = topologic.VertexUtility.AdjacentCells(item, hostTopology, adjacentTopologies)
			except:
				try:
					_ = item.Cells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "CellComplex":
			try:
				_ = topologic.VertexUtility.AdjacentCellComplexes(item, hostTopology, adjacentTopologies)
			except:
				try:
					_ = item.CellComplexes(hostTopology, adjacentTopologies)
				except:
					error = True
	elif itemType == topologic.Edge.Type():
		if topologyType == "Vertex":
			try:
				_ = item.Vertices(hostTopology, adjacentTopologies)
			except:
				error = True
		elif topologyType == "Edge":
			try:
				_ = item.AdjacentEdges(hostTopology, adjacentTopologies)
			except:
				error = True
		elif topologyType == "Wire":
			try:
				_ = topologic.EdgeUtility.AdjacentWires(item, adjacentTopologies)
			except:
				try:
					_ = item.Wires(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Face":
			try:
				_ = topologic.EdgeUtility.AdjacentFaces(item, adjacentTopologies)
			except:
				try:
					_ = item.Faces(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Shell":
			try:
				_ = topologic.EdgeUtility.AdjacentShells(adjacentTopologies)
			except:
				try:
					_ = item.Shells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Cell":
			try:
				_ = topologic.EdgeUtility.AdjacentCells(adjacentTopologies)
			except:
				try:
					_ = item.Cells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "CellComplex":
			try:
				_ = topologic.EdgeUtility.AdjacentCellComplexes(adjacentTopologies)
			except:
				try:
					_ = item.CellComplexes(hostTopology, adjacentTopologies)
				except:
					error = True
	elif itemType == topologic.Wire.Type():
		if topologyType == "Vertex":
			try:
				_ = topologic.WireUtility.AdjacentVertices(item, adjacentTopologies)
			except:
				try:
					_ = item.Vertices(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Edge":
			try:
				_ = topologic.WireUtility.AdjacentEdges(item, adjacentTopologies)
			except:
				try:
					_ = item.Edges(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Wire":
			try:
				_ = topologic.WireUtility.AdjacentWires(item, adjacentTopologies)
			except:
				try:
					_ = item.Wires(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Face":
			try:
				_ = topologic.WireUtility.AdjacentFaces(item, adjacentTopologies)
			except:
				try:
					_ = item.Faces(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Shell":
			try:
				_ = topologic.WireUtility.AdjacentShells(adjacentTopologies)
			except:
				try:
					_ = item.Shells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Cell":
			try:
				_ = topologic.WireUtility.AdjacentCells(adjacentTopologies)
			except:
				try:
					_ = item.Cells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "CellComplex":
			try:
				_ = topologic.WireUtility.AdjacentCellComplexes(adjacentTopologies)
			except:
				try:
					_ = item.CellComplexes(hostTopology, adjacentTopologies)
				except:
					error = True
	elif itemType == topologic.Face.Type():
		if topologyType == "Vertex":
			try:
				_ = topologic.FaceUtility.AdjacentVertices(item, adjacentTopologies)
			except:
				try:
					_ = item.Vertices(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Edge":
			try:
				_ = topologic.FaceUtility.AdjacentEdges(item, adjacentTopologies)
			except:
				try:
					_ = item.Edges(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Wire":
			try:
				_ = topologic.FaceUtility.AdjacentWires(item, adjacentTopologies)
			except:
				try:
					_ = item.Wires(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Face":
			_ = item.AdjacentFaces(hostTopology, adjacentTopologies)
			print("Success!!")
		elif topologyType == "Shell":
			try:
				_ = topologic.FaceUtility.AdjacentShells(adjacentTopologies)
			except:
				try:
					_ = item.Shells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Cell":
			try:
				_ = topologic.FaceUtility.AdjacentCells(adjacentTopologies)
			except:
				try:
					_ = item.Cells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "CellComplex":
			try:
				_ = topologic.FaceUtility.AdjacentCellComplexes(adjacentTopologies)
			except:
				try:
					_ = item.CellComplexes(hostTopology, adjacentTopologies)
				except:
					error = True
	elif itemType == topologic.Shell.Type():
		if topologyType == "Vertex":
			try:
				_ = topologic.ShellUtility.AdjacentVertices(item, adjacentTopologies)
			except:
				try:
					_ = item.Vertices(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Edge":
			try:
				_ = topologic.ShellUtility.AdjacentEdges(item, adjacentTopologies)
			except:
				try:
					_ = item.Edges(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Wire":
			try:
				_ = topologic.ShellUtility.AdjacentWires(item, adjacentTopologies)
			except:
				try:
					_ = item.Wires(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Face":
			try:
				_ = topologic.ShellUtility.AdjacentFaces(item, adjacentTopologies)
			except:
				try:
					_ = item.Faces(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Shell":
			try:
				_ = topologic.ShellUtility.AdjacentShells(adjacentTopologies)
			except:
				try:
					_ = item.Shells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Cell":
			try:
				_ = topologic.ShellUtility.AdjacentCells(adjacentTopologies)
			except:
				try:
					_ = item.Cells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "CellComplex":
			try:
				_ = topologic.ShellUtility.AdjacentCellComplexes(adjacentTopologies)
			except:
				try:
					_ = item.CellComplexes(hostTopology, adjacentTopologies)
				except:
					error = True
	elif itemType == topologic.Cell.Type():
		if topologyType == "Vertex":
			try:
				_ = topologic.CellUtility.AdjacentVertices(item, adjacentTopologies)
			except:
				try:
					_ = item.Vertices(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Edge":
			try:
				_ = topologic.CellUtility.AdjacentEdges(item, adjacentTopologies)
			except:
				try:
					_ = item.Edges(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Wire":
			try:
				_ = topologic.CellUtility.AdjacentWires(item, adjacentTopologies)
			except:
				try:
					_ = item.Wires(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Face":
			try:
				_ = topologic.CellUtility.AdjacentFaces(item, adjacentTopologies)
			except:
				try:
					_ = item.Faces(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Shell":
			try:
				_ = topologic.CellUtility.AdjacentShells(adjacentTopologies)
			except:
				try:
					_ = item.Shells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "Cell":
			try:
				_ = item.AdjacentCells(hostTopology, adjacentTopologies)
			except:
				try:
					_ = item.Cells(hostTopology, adjacentTopologies)
				except:
					error = True
		elif topologyType == "CellComplex":
			try:
				_ = topologic.CellUtility.AdjacentCellComplexes(adjacentTopologies)
			except:
				try:
					_ = item.CellComplexes(hostTopology, adjacentTopologies)
				except:
					error = True
	elif itemType == topologic.CellComplex.Type():
		if topologyType == "Vertex":
			try:
				_ = item.Vertices(hostTopology, adjacentTopologies)
			except:
				error = True
		elif topologyType == "Edge":
			try:
				_ = item.Edges(hostTopology, adjacentTopologies)
			except:
				error = True
		elif topologyType == "Wire":
			try:
				_ = item.Wires(hostTopology, adjacentTopologies)
			except:
				error = True
		elif topologyType == "Face":
			try:
				_ = item.Faces(hostTopology, adjacentTopologies)
			except:
				error = True
		elif topologyType == "Shell":
			try:
				_ = item.Shells(hostTopology, adjacentTopologies)
			except:
				error = True
		elif topologyType == "Cell":
			try:
				_ = item.Cells(hostTopology, adjacentTopologies)
			except:
				error = True
		elif topologyType == "CellComplex":
			raise Exception("Topology.AdjacentTopologies - Error: Cannot search for adjacent topologies of a CellComplex")
	elif itemType == topologic.Cluster.Type():
		raise Exception("Topology.AdjacentTopologies - Error: Cannot search for adjacent topologies of a Cluster")
	if error:
		raise Exception("Topology.AdjacentTopologies - Error: Failure in search for adjacent topologies of type "+topologyType)
	return adjacentTopologies

def recur(input, hostTopology, topologyType):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem, hostTopology, topologyType))
	else:
		output = processItem(input, hostTopology, topologyType)
	return output

topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4), ("Cell", "Cell", "", 6)]

class SvTopologyAdjacentTopologies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the adjacent topologies, based on the selected type, of the input Topology    
	"""
	bl_idname = 'SvTopologyAdjacentTopologies'
	bl_label = 'Topology.AdjacentTopologies'
	adjacentTopologyType: EnumProperty(name="Adjacent Topology Type", description="Specify adjacent topology type", default="Vertex", items=topologyTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Host Topology')
		self.outputs.new('SvStringsSocket', 'Adjacent Topologies')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, "adjacentTopologyType",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Adjacent Topologies'].sv_set([])
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		hostTopology = self.inputs['Host Topology'].sv_get(deepcopy=False)[0] #accept only one host topology
		outputs = recur(inputs, hostTopology, self.adjacentTopologyType)
		if(len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['Adjacent Topologies'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyAdjacentTopologies)

def unregister():
	bpy.utils.unregister_class(SvTopologyAdjacentTopologies)
