import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time

def processItem(item):
	topology, topologyType = item
	if topology.GetTypeAsString() == topologyType:
		return [topology]
	subtopologies = []
	if topologyType == "Vertex":
		_ = topology.Vertices(None, subtopologies)
	elif topologyType == "Edge":
		_ = topology.Edges(None, subtopologies)
	elif topologyType == "Wire":
		_ = topology.Wires(None, subtopologies)
	elif topologyType == "Face":
		_ = topology.Faces(None, subtopologies)
	elif topologyType == "Shell":
		_ = topology.Shells(None, subtopologies)
	elif topologyType == "Cell":
		_ = topology.Cells(None, subtopologies)
	elif topologyType == "CellComplex":
		_ = topology.CellComplexes(None, subtopologies)
	elif topologyType == "Cluster":
		_ = topology.Clusters(None, subtopologies)
	elif topologyType == "Aperture":
		_ = topology.Apertures(None, subtopologies)
	else:
		raise Exception("Topology.Subtopologies - Error: Could not retrieve the requested SubTopologies of type "+topologyType)
	return subtopologies

def recur(topology, topologyType):
	output = []
	if topology == None:
		return []
	if isinstance(topology, list):
		for anItem in topology:
			output.append(recur(anItem, topologyType))
	else:
		output = processItem([topology, topologyType])
	return output

topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7), ("Cluster", "Cluster", "", 8), ("Aperture", "Aperture", "", 9)]

class SvTopologySubTopologies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the subtopologies, based on the selected type, of the input Topology    
	"""
	bl_idname = 'SvTopologySubTopologies'
	bl_label = 'Topology.SubTopologies'
	subtopologyType: EnumProperty(name="Subtopology Type", description="Specify subtopology type", default="Vertex", items=topologyTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'SubTopologies')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, "subtopologyType",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['SubTopologies'].sv_set([])
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)
		outputs = recur(inputs, self.subtopologyType)
		if(len(outputs) == 1):
			outputs = outputs[0]
		self.outputs['SubTopologies'].sv_set(outputs)
		end = time.time()
		print("Topology.SubTopologies ("+self.subtopologyType+") Operation consumed "+str(round((end - start)*1000,0))+" ms")

def register():
	bpy.utils.register_class(SvTopologySubTopologies)

def unregister():
	bpy.utils.unregister_class(SvTopologySubTopologies)
