import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication
import time

def processItem(item):
	topology, subTopologyType = item
	if topology.GetTypeAsString() == subTopologyType:
		return [topology]
	subTopologies = []
	if subTopologyType == "Vertex":
		_ = topology.Vertices(None, subTopologies)
	elif subTopologyType == "Edge":
		_ = topology.Edges(None, subTopologies)
	elif subTopologyType == "Wire":
		_ = topology.Wires(None, subTopologies)
	elif subTopologyType == "Face":
		_ = topology.Faces(None, subTopologies)
	elif subTopologyType == "Shell":
		_ = topology.Shells(None, subTopologies)
	elif subTopologyType == "Cell":
		_ = topology.Cells(None, subTopologies)
	elif subTopologyType == "CellComplex":
		_ = topology.CellComplexes(None, subTopologies)
	elif subTopologyType == "Cluster":
		_ = topology.Clusters(None, subTopologies)
	elif subTopologyType == "Aperture":
		_ = topology.Apertures(subTopologies)
	return subTopologies

def recur(input, subTopologyType):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem, subTopologyType))
	else:
		output = processItem([input, subTopologyType])
	return output

subTopologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7), ("Cluster", "Cluster", "", 8), ("Aperture", "Aperture", "", 9)]

class SvTopologySubTopologies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the subTopologies, based on the selected type, of the input Topology    
	"""
	bl_idname = 'SvTopologySubTopologies'
	bl_label = 'Topology.SubTopologies'
	bl_icon = 'SELECT_DIFFERENCE'
	
	SubTopologyType: EnumProperty(name="Subtopology Type", description="Specify subtopology type", default="Vertex", items=subTopologyTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'SubTopologies')
		self.width = 200
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
		split.row().label(text="SubTopologyType")
		split.row().prop(self, "SubTopologyType",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		input = self.inputs[0].sv_get(deepcopy=False)
		output = recur(input, self.SubTopologyType)
		if not isinstance(output, list):
			output = [output]
		self.outputs['SubTopologies'].sv_set(output)

def register():
	bpy.utils.register_class(SvTopologySubTopologies)

def unregister():
	bpy.utils.unregister_class(SvTopologySubTopologies)
