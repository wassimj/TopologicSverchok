import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time

def topologyTypeID(topologyType):
	typeID = None
	try:
		if topologyType == "Vertex":
			typeID = topologic.Vertex.Type()
		elif topologyType == "Edge":
			typeID = topologic.Edge.Type()
		elif topologyType == "Wire":
			typeID = topologic.Wire.Type()
		elif topologyType == "Face":
			typeID = topologic.Face.Type()
		elif topologyType == "Shell":
			typeID = topologic.Shell.Type()
		elif topologyType == "Cell":
			typeID = topologic.Cell.Type()
		elif topologyType == "CellComplex":
			typeID = topologic.CellComplex.Type()
		elif topologyType == "Cluster":
			typeID = topologic.Cluster.Type()
	except:
		typeID = None
	return typeID

def processItem(item, hostTopology, topologyType):
	adjacentTopologies = []
	_ = topologic.Topology.Navigate(item, hostTopology, adjacentTopologies)
	return adjacentTopologies

def processItem2(item, hostTopology, topologyType):
	adjacentTopologies = []
	error = False
	itemType = item.Type()
	if itemType == topologic.Vertex.Type():
		if topologyType == "Vertex":
			try:
				_ = item.AdjacentVertices(hostTopology, adjacentTopologies)
			except:
				error = True
		else:
			try:
				_ = item.UpwardNavigation(hostTopology, topologyTypeID(topologyType), adjacentTopologies)
			except:
				error = True
	elif itemType == topologic.Edge.Type():
		if topologyType == "Vertex":
			try:
				_ = item.Vertices(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Edge":
			try:
				_ = item.AdjacentEdges(hostTopology, adjacentTopologies)
			except:
				error = True
		else:
			try:
				_ = item.UpwardNavigation(hostTopology, topologyTypeID(topologyType), adjacentTopologies)
			except:
				error = True
	elif itemType == topologic.Wire.Type():
		if topologyType == "Vertex":
			try:
				_ = item.Vertices(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Edge":
			try:
				_ = item.Edges(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Wire":
			raise Exception("Topology.Navigate - Error: Cannot search for adjacent Wires of a Wire. Use Faces instead.")
		else:
			try:
				_ = item.UpwardNavigation(hostTopology, topologyTypeID(topologyType), adjacentTopologies)
			except:
				error = True
	elif itemType == topologic.Face.Type():
		if topologyType == "Vertex":
			try:
				_ = item.Vertices(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Edge":
			try:
				_ = item.Edges(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Wire":
			try:
				_ = item.Wires(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Face":
			try:
				_ = item.AdjacentFaces(hostTopology, adjacentTopologies)
			except:
				error = True
		else:
			try:
				_ = item.UpwardNavigation(hostTopology, topologyTypeID(topologyType), adjacentTopologies)
			except:
				error = True
	elif itemType == topologic.Shell.Type():
		if topologyType == "Vertex":
			try:
				_ = item.Vertices(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Edge":
			try:
				_ = item.Edges(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Wire":
			try:
				_ = item.Wires(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Face":
			try:
				_ = item.Faces(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Shell":
			raise Exception("Topology.Navigate - Error: Cannot search for adjacent Shells of a Shell. Use Cells instead.")
		else:
			try:
				_ = item.UpwardNavigation(hostTopology, topologyTypeID(topologyType), adjacentTopologies)
			except:
				error = True
	elif itemType == topologic.Cell.Type():
		if topologyType == "Vertex":
			try:
				_ = item.Vertices(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Edge":
			try:
				_ = item.Edges(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Wire":
			try:
				_ = item.Wires(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Face":
			try:
				_ = item.Faces(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Shell":
			try:
				_ = item.Shells(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Cell":
			try:
				_ = item.AdjacentCells(hostTopology, adjacentTopologies)
			except:
				error = True
		else:
			try:
				_ = item.UpwardNavigation(hostTopology, topologyTypeID(topologyType), adjacentTopologies)
			except:
				error = True
	elif itemType == topologic.CellComplex.Type():
		if topologyType == "Vertex":
			try:
				_ = item.Vertices(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Edge":
			try:
				_ = item.Edges(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Wire":
			try:
				_ = item.Wires(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Face":
			try:
				_ = item.Faces(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Shell":
			try:
				_ = item.Shells(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Cell":
			try:
				_ = item.Cells(adjacentTopologies)
			except:
				error = True
		elif topologyType == "CellComplex":
			raise Exception("Topology.Navigate - Error: Cannot search for adjacent CellComplexes of a CellComplex")
	elif itemType == topologic.Cluster.Type():
		if topologyType == "Vertex":
			try:
				_ = item.Vertices(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Edge":
			try:
				_ = item.Edges(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Wire":
			try:
				_ = item.Wires(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Face":
			try:
				_ = item.Faces(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Shell":
			try:
				_ = item.Shells(adjacentTopologies)
			except:
				error = True
		elif topologyType == "Cell":
			try:
				_ = item.Cells(adjacentTopologies)
			except:
				error = True
		elif topologyType == "CellComplex":
			try:
				_ = item.CellComplexes(adjacentTopologies)
			except:
				error = True
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

topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7)]

class SvTopologyNavigate(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the topologies, found within the host Topology, associated with the input Topology    
	"""
	bl_idname = 'SvTopologyNavigate'
	bl_label = 'Topology.Navigate'
	topologyType: EnumProperty(name="Topology Type", description="Specify Topology type", default="Vertex", items=topologyTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Host Topology')
		self.outputs.new('SvStringsSocket', 'Topologies')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, "topologyType",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topologies'].sv_set([])
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		if (self.inputs['Host Topology']).is_linked:
			hostTopology = self.inputs['Host Topology'].sv_get(deepcopy=False)[0] #accept only one host Topology
		else:
			hostTopology = None
		outputs = recur(inputs, hostTopology, self.topologyType)
		if(len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['Topologies'].sv_set(outputs)
		end = time.time()
		print("Topology.Navigate ("+self.topologyType+") Operation consumed "+str(round((end - start)*1000,0))+" ms")

def register():
	bpy.utils.register_class(SvTopologyNavigate)

def unregister():
	bpy.utils.unregister_class(SvTopologyNavigate)
