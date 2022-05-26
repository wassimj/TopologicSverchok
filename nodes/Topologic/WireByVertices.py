import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
from . import Replication, TopologySelfMerge

def processItem(item):
	vertices, close = item
	wire = None
	edges = []
	for i in range(len(vertices)-1):
		v1 = vertices[i]
		v2 = vertices[i+1]
		try:
			e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
			if e:
				edges.append(e)
		except:
			continue
	if close:
		v1 = vertices[-1]
		v2 = vertices[0]
		try:
			e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
			if e:
				edges.append(e)
		except:
			pass
	if len(edges) > 0:
		c = topologic.Cluster.ByTopologies(edges, False)
		return TopologySelfMerge.processItem(c)
	else:
		return None

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvWireByVertices(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Wire from the list of input Vertices. The Vertices are assumed to be ordered.    
	"""
	bl_idname = 'SvWireByVertices'
	bl_label = 'Wire.ByVertices'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	CloseProp: BoolProperty(name="Close", default=True, update=updateNode)


	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertices')
		self.inputs.new('SvStringsSocket', 'Close').prop_name = 'CloseProp'
		self.outputs.new('SvStringsSocket', 'Wire')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		vertexList = self.inputs['Vertices'].sv_get(deepcopy=True)
		if isinstance(vertexList[0], list) == False:
			vertexList = [vertexList]
		closeList = self.inputs['Close'].sv_get(deepcopy=True)
		closeList = Replication.flatten(closeList)
		inputs = [vertexList, closeList]
		if ((self.Replication) == "Default"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = Replication.repeat(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(Replication.interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Wire'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvWireByVertices)

def unregister():
    bpy.utils.unregister_class(SvWireByVertices)
