import bpy
from bpy.props import FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def projectVertex(vertex, face, vList):
	if topologic.FaceUtility.IsInside(face, vertex, 0.001):
		return vertex
	d = topologic.VertexUtility.Distance(vertex, face)*10
	far_vertex = topologic.TopologyUtility.Translate(vertex, vList[0]*d, vList[1]*d, vList[2]*d)
	if topologic.VertexUtility.Distance(vertex, far_vertex) > 0.001:
		e = topologic.Edge.ByStartVertexEndVertex(vertex, far_vertex)
		pv = face.Intersect(e, False)
		return pv
	else:
		return None

def processItem(item):
	wire, face, direction = item
	large_face = topologic.TopologyUtility.Scale(face, face.CenterOfMass(), 500, 500, 500)
	try:
		vList = [direction.X(), direction.Y(), direction.Z()]
	except:
		try:
			vList = [direction[0], direction[1], direction[2]]
		except:
			raise Exception("Wire.Project - Error: Could not get the vector from the input direction")
	projected_wire = None
	edges = []
	_ = wire.Edges(None, edges)
	projected_edges = []

	if large_face:
		if (large_face.Type() == topologic.Face.Type()):
			for edge in edges:
				if edge:
					if (edge.Type() == topologic.Edge.Type()):
						sv = edge.StartVertex()
						ev = edge.EndVertex()

						psv = projectVertex(sv, large_face, direction)
						pev = projectVertex(ev, large_face, direction)
						if psv and pev:
							try:
								pe = topologic.Edge.ByStartVertexEndVertex(psv, pev)
								projected_edges.append(pe)
							except:
								continue
	w = topologic.Wire.ByEdges(projected_edges)
	if w and w.IsClosed():
		f = topologic.Face.ByExternalBoundary(w)
		f = f.Intersect(face, False)
		faces = []
		_ = f.Faces(None, faces)
		f = faces[0]
		if f:
			edges = []
			w = f.ExternalBoundary()
	return w

lacing = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Lace", "Lace", "", 5)]

class SvWireProject(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Projects the input Wire on the input Face
	"""
	bl_idname = 'SvWireProject'
	bl_label = 'Wire.Project'
	Lacing: EnumProperty(name="Lacing", description="Lacing", default="Default", items=lacing, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'Direction')
		self.outputs.new('SvStringsSocket', 'Wire')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Lacing",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		wireList = self.inputs['Wire'].sv_get(deepcopy=False)
		wireList = Replication.flatten(wireList)
		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		faceList = Replication.flatten(faceList)
		directionList = self.inputs['Direction'].sv_get(deepcopy=False)
		directionList = Replication.flatten(directionList)
		inputs = [wireList, faceList, directionList]
		if ((self.Lacing) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Lacing) == "Iterate"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Lacing) == "Repeat") or ((self.Lacing) == "Default"):
			inputs = Replication.repeat(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Lacing) == "Lace"):
			inputs = list(Replication.interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Wire'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvWireProject)

def unregister():
	bpy.utils.unregister_class(SvWireProject)
