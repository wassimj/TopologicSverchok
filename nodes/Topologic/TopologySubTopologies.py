import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(item, topologyType):
	subtopologies = []
	try:
		if topologyType == "Vertex":
			_ = item.Vertices(subtopologies)
		elif topologyType == "Edge":
			_ = item.Edges(subtopologies)
		elif topologyType == "Wire":
			_ = item.Wires(subtopologies)
		elif topologyType == "Face":
			_ = item.Faces(subtopologies)
		elif topologyType == "Shell":
			_ = item.Shells(subtopologies)
		elif topologyType == "Cell":
			_ = item.Cells(subtopologies)
		elif topologyType == "CellComplex":
			_ = item.CellComplexes(subtopologies)
		elif topologyType == "Aperture":
			_ = item.Apertures(subtopologies)
	except:
		raise Exception("Topology.Subtopologies - Error: Could not retrieve the requested SubTopologies")
	return subtopologies

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

topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7), ("Aperture", "Aperture", "", 8)]

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

def register():
	bpy.utils.register_class(SvTopologySubTopologies)

def unregister():
	bpy.utils.unregister_class(SvTopologySubTopologies)
