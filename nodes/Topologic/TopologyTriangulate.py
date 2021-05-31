import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def triangulateFace(face):
	faceTriangles = cppyy.gbl.std.list[topologic.Face.Ptr]()
	for i in range(0,5,1):
		try:
			_ = topologic.FaceUtility.Triangulate(face, float(i)*0.1, faceTriangles)
			return faceTriangles
		except:
			continue
	faceTrinagles.push_back(face)
	return faceTriangles

def processItem(topology, tolerance):
	t = topology.GetType()
	if (t == 1) or (t == 2) or (t == 4) or (t == 128):
		return topology
	topologyFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	_ = topology.Faces(topologyFaces)
	faceTriangles = cppyy.gbl.std.list[topologic.Face.Ptr]()
	for aFace in topologyFaces:
		triFaces = triangulateFace(aFace)
		for triFace in triFaces:
			faceTriangles.push_back(triFace)
	if t == 8 or t == 16: # Face or Shell
		return topologic.Shell.ByFaces(faceTriangles, tolerance)
	elif t == 32: # Cell
		return topologic.Cell.ByFaces(faceTriangles, tolerance)
	elif t == 64: #CellComplex
		return topologic.CellComplex.ByFaces(faceTriangles, tolerance)

class SvTopologyTriangulate(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a Topology with triangulated faces of the input Topology
	"""
	bl_idname = 'SvTopologyTriangulate'
	bl_label = 'Topology.Triangulate'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		topologyList = flatten(topologyList)
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0][0]
		outputs = []
		for aTopology in topologyList:
			outputs.append(processItem(aTopology, tol))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyTriangulate)

def unregister():
	bpy.utils.unregister_class(SvTopologyTriangulate)
