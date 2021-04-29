import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

def processItem(item, topologyType):
	subtopologies = []
	try:
		if topologyType == "Vertex":
			vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			_ = item.Vertices(vertices)
			subtopologies = list(vertices)
		elif topologyType == "Edge":
			edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = item.Edges(edges)
			subtopologies = list(edges)
		elif topologyType == "Wire":
			wires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
			_ = item.Wires(wires)
			subtopologies = list(wires)
		elif topologyType == "Face":
			faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
			_ = item.Faces(faces)
			subtopologies = list(faces)
		elif topologyType == "Shell":
			shells = cppyy.gbl.std.list[topologic.Shell.Ptr]()
			_ = item.Shells(shells)
			subtopologies = list(shells)
		elif topologyType == "Cell":
			cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
			_ = item.Cells(cells)
			subtopologies = list(cells)
		elif topologyType == "CellComplex":
			cellcomplexes = cppyy.gbl.std.list[topologic.CellComplex.Ptr]()
			_ = item.CellComplexes(cellcomplexes)
			subtopologies = list(cellcomplexes)
		elif topologyType == "Aperture":
			apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
			_ = item.Apertures(apertures)
			subtopologies = list(apertures)
	except:
		subtopologies = []
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
