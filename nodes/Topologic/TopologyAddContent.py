import bpy
from bpy.props import StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def processItem(item, targetType):
	topology = item[0]
	contents = Replication.flatten(item[1])
	t = 0
	if targetType == "Vertex":
		t = topologic.Vertex.Type()
	elif targetType == "Edge":
		t = topologic.Edge.Type()
	elif targetType == "Wire":
		t = topologic.Wire.Type()
	elif targetType == "Face":
		t = topologic.Face.Type()
	elif targetType == "Shell":
		t = topologic.Shell.Type()
	elif targetType == "Cell":
		t = topologic.Cell.Type()
	elif targetType == "CellComplex":
		t = topologic.CellComplex.Type()
	elif targetType == "Host Topology":
		t = 0
	return topology.AddContents(contents, t)

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7), ("Host Topology", "Host Topology", "", 8)]


class SvTopologyAddContent(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Adds the input Topology content to the input Topology. If the type is set to Topology, the content will be added to the input topology. Otherwise, it will be added to the closest sub-topology of the specified type.   
	"""
	bl_idname = 'SvTopologyAddContent'
	bl_label = 'Topology.AddContent'
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	TargetType: EnumProperty(name="Topology Target", description="Specify topology target", default="Host Topology", items=topologyTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Content')
		self.outputs.new('SvStringsSocket', 'Topology')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "TargetType",text="Add Content To")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return

		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		contentList = self.inputs['Content'].sv_get(deepcopy=True)
		topologyList = Replication.flatten(topologyList)
		inputs = [topologyList, contentList]
		if ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif (self.Replication == "Iterate" or self.Replication == "Default"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = Replication.repeat(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, self.TargetType))
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvTopologyAddContent)

def unregister():
    bpy.utils.unregister_class(SvTopologyAddContent)
