import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

from . import CellByFaces

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item, tol):
	faces = [topologic.Face.ByExternalBoundary(item[0])]
	faces.append(topologic.Face.ByExternalBoundary(item[-1]))
	for i in range(len(item)-1):
		wire1 = item[i]
		wire2 = item[i+1]
		w1_edges = []
		_ = wire1.Edges(None, w1_edges)
		w2_edges = []
		_ = wire2.Edges(None, w2_edges)
		if len(w1_edges) != len(w2_edges):
			raise Exception("Shell.ByLoft - Error: The two wires do not have the same number of edges.")
		for j in range (len(w1_edges)):
			e1 = w1_edges[j]
			e2 = w2_edges[j]
			e3 = None
			e4 = None
			try:
				e3 = topologic.Edge.ByStartVertexEndVertex(e1.StartVertex(), e2.StartVertex())
			except:
				e4 = topologic.Edge.ByStartVertexEndVertex(e1.EndVertex(), e2.EndVertex())
				faces.append(topologic.Face.ByExternalBoundary(topologic.Wire.ByEdges([e1, e2, e4])))
			try:
				e4 = topologic.Edge.ByStartVertexEndVertex(e1.EndVertex(), e2.EndVertex())
			except:
				e3 = topologic.Edge.ByStartVertexEndVertex(e1.StartVertex(), e2.StartVertex())
				faces.append(topologic.Face.ByExternalBoundary(topologic.Wire.ByEdges([e1, e2, e3])))
			if e3 and e4:
				e5 = topologic.Edge.ByStartVertexEndVertex(e1.StartVertex(), e2.EndVertex())
				faces.append(topologic.Face.ByExternalBoundary(topologic.Wire.ByEdges([e1, e5, e4])))
				faces.append(topologic.Face.ByExternalBoundary(topologic.Wire.ByEdges([e2, e5, e3])))
	try:
		return CellByFaces.processItem(faces, tol)
	except:
		return topologic.Cluster.ByTopologies(faces)
	

class SvCellByLoft(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cell by lofting through the input Wires. The Wires must be closed and ordered
	"""
	bl_idname = 'SvCellByLoft'
	bl_label = 'Cell.ByLoft'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wires')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		wiresList = self.inputs['Wires'].sv_get(deepcopy=False)
		tol = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)[0][0]
		if isinstance(wiresList[0], list) == False:
			wiresList = [wiresList]
		outputs = []
		for wireList in wiresList:
			outputs.append(processItem(wireList, tol))
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellByLoft)

def unregister():
	bpy.utils.unregister_class(SvCellByLoft)
