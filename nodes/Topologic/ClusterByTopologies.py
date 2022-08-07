import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def processItem(item):
	assert isinstance(item, list), "Cluster.ByTopologies - Error: Input is not a list"
	topologyList = [x for x in item if isinstance(x, topologic.Topology)]
	return topologic.Cluster.ByTopologies(topologyList, False)

def recur(item):
	output = []
	if item == None:
		return []
	if isinstance(item[0], list):
		for subItem in item:
			output.append(recur(subItem))
	else:
		output = processItem(item)
	return output

class SvClusterByTopologies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cluster from the list of input Topologies  
	"""
	bl_idname = 'SvClusterByTopologies'
	bl_label = 'Cluster.ByTopologies'
	bl_icon = 'SELECT_DIFFERENCE'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topologies')
		self.outputs.new('SvStringsSocket', 'Cluster')
		self.width = 175
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		input = self.inputs[0].sv_get(deepcopy=False)
		output = recur(input)
		if not isinstance(output, list):
			output = [output]
		self.outputs['Cluster'].sv_set(output)

def register():
    bpy.utils.register_class(SvClusterByTopologies)

def unregister():
    bpy.utils.unregister_class(SvClusterByTopologies)
