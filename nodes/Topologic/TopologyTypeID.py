import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def processItem(topologyType):
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


topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7),("Cluster", "Cluster", "", 8)]

class SvTopologyTypeID(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the ID of the selected Topology Type    
	"""
	bl_idname = 'SvTopologyTypeID'
	bl_label = 'Topology.TypeID'
	TypeID: EnumProperty(name="TypeID", description="Specify topology type", default="Vertex", items=topologyTypes, update=updateNode)

	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Type')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, "TypeID",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		output = processItem(self.TypeID)
		self.outputs['Type'].sv_set([output])

def register():
	bpy.utils.register_class(SvTopologyTypeID)

def unregister():
	bpy.utils.unregister_class(SvTopologyTypeID)
