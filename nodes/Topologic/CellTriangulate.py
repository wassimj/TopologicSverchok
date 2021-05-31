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

def processItem(cell):
	cellFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	_ = cell.Faces(cellFaces)
	faceTriangles = cppyy.gbl.std.list[topologic.Face.Ptr]()
	for aFace in cellFaces:
		triFaces = triangulateFace(aFace)
		for triFace in triFaces:
			faceTriangles.push_back(triFace)
	return topologic.Cell.ByFaces(faceTriangles)

class SvCellTriangulate(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a Cell with triangulated faces of the input Cell
	"""
	bl_idname = 'SvCellTriangulate'
	bl_label = 'Cell.Triangulate'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cell')
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		cellList = self.inputs['Cell'].sv_get(deepcopy=False)
		cellList = flatten(cellList)
		outputs = []
		for aCell in cellList:
			outputs.append(processItem(aCell))
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellTriangulate)

def unregister():
	bpy.utils.unregister_class(SvCellTriangulate)
