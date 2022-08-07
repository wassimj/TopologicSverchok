import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic
from . import Replication

def processItem(item):
	topology = item[0]
	context = item[1]
	aperture = None
	try:
		aperture = topologic.Aperture.ByTopologyContext(topology, context)
	except:
		aperture = None
	return aperture

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvApertureByTopologyContext(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates an Aperture from the input Topology and Context   
	"""
	bl_idname = 'SvApertureByTopologyContext'
	bl_label = 'Aperture.ByTopologyContext'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Context')
		self.outputs.new('SvStringsSocket', 'Aperture')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.separator()

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		contextList = self.inputs['Context'].sv_get(deepcopy=True)
		topologyList = Replication.flatten(topologyList)
		contextList = Replication.flatten(contextList)
		inputs = [topologyList, contextList]
		inputs = Replication.replicateInputs(inputs, self.Replication)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Aperture'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvApertureByTopologyContext)

def unregister():
    bpy.utils.unregister_class(SvApertureByTopologyContext)
