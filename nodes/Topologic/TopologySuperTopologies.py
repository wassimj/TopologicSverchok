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
	superTopologies = []
	typeID = topologyTypeID(topologyType)
	if item.Type() >= typeID:
		raise Exception("TopologySuperTopologies - Error: the requested Topology Type (" + topologyType + ") cannot be a Super Topology of the input Topology Type (" + item.GetTypeAsString() + ")")
	elif typeID == topologic.Vertex.Type():
		item.Vertices(hostTopology, superTopologies)
	elif typeID == topologic.Edge.Type():
		item.Edges(hostTopology, superTopologies)
	elif typeID == topologic.Wire.Type():
		item.Wires(hostTopology, superTopologies)
	elif typeID == topologic.Face.Type():
		item.Faces(hostTopology, superTopologies)
	elif typeID == topologic.Shell.Type():
		item.Shells(hostTopology, superTopologies)
	elif typeID == topologic.Cell.Type():
		item.Cells(hostTopology, superTopologies)
	elif typeID == topologic.CellComplex.Type():
		item.CellComplexes(hostTopology, superTopologies)
	elif typeID == topologic.Cluster.Type():
		item.Cluster(hostTopology, superTopologies)
	else:
		raise Exception("TopologySuperTopologies - Error: the requested Topology Type (" + topologyType + ") could not be found.")
	return superTopologies


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

class SvTopologySuperTopologies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the supertopologies found within the host Topology, based on the selected type of the input Topology    
	"""
	bl_idname = 'SvTopologySuperTopologies'
	bl_label = 'Topology.SuperTopologies'
	supertopologyType: EnumProperty(name="Topology Type", description="Specify Topology type", default="CellComplex", items=topologyTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Host Topology')
		self.outputs.new('SvStringsSocket', 'Super Topologies')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, "supertopologyType",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Super Topologies'].sv_set([])
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		hostTopology = self.inputs['Host Topology'].sv_get(deepcopy=False)[0] #accept only one host Topology
		outputs = recur(inputs, hostTopology, self.supertopologyType)
		if(len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['Super Topologies'].sv_set(outputs)
		end = time.time()
		print("Topology.SuperTopologies ("+self.supertopologyType+") Operation consumed "+str(round((end - start)*1000,0))+" ms")

def register():
	bpy.utils.register_class(SvTopologySuperTopologies)

def unregister():
	bpy.utils.unregister_class(SvTopologySuperTopologies)
