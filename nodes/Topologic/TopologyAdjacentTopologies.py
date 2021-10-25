import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item, topologyType):
	adjacentTopologies = []
	error = False
	if topologyType == "Vertex":
		try:
			_ = item.AdjacentVertices(adjacentTopologies)
		except:
			try:
				_ = item.Vertices(adjacentTopologies)
			except:
				error = True
	elif topologyType == "Edge":
		try:
			_ = item.AdjacentEdges(adjacentTopologies)
		except:
			try:
				_ = item.Edges(adjacentTopologies)
			except:
				error = True
	elif topologyType == "Wire":
		try:
			_ = item.AdjacentWires(adjacentTopologies)
		except:
			try:
				_ = item.Wires(adjacentTopologies)
			except:
				error = True
	elif topologyType == "Face":
		try:
			_ = item.AdjacentFaces(adjacentTopologies)
		except:
			try:
				_ = item.Faces(adjacentTopologies)
			except:
				error = True
	elif topologyType == "Shell":
		try:
			_ = item.AdjacentShells(adjacentTopologies)
		except:
			try:
				_ = item.Shells(adjacentTopologies)
			except:
				error = True
	elif topologyType == "Cell":
		try:
			_ = item.AdjacentCells(adjacentTopologies)
		except:
			try:
				_ = item.Cells(adjacentTopologies)
			except:
				error = True
	elif topologyType == "CellComplex":
		try:
			_ = item.AdjacentCellComplexes(adjacentTopologies)
		except:
			try:
				_ = item.CellComplexes(adjacentTopologies)
			except:
				error = True
	if error:
		raise Exception("Topology.AdjacentTopologies - Error: Failure in search for adjacent topologies of type "+topologyType)
	return adjacentTopologies

def recur(input, topologyType):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem, topologyType))
	else:
		output = processItem(input, topologyType)
	return output

topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7)]

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
		self.outputs.new('SvStringsSocket', 'Topologies')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, "adjacentTopologyType",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['SubTopologies'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = recur(inputs, self.adjacentTopologyType)
		if(len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['Topologies'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyAdjacentTopologies)

def unregister():
	bpy.utils.unregister_class(SvTopologyAdjacentTopologies)
