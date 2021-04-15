import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy
import time

def matchLengths(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

# Adapted From https://johnlekberg.com/blog/2020-04-17-kd-tree.html
import collections
import operator
def SED(a, b):
	"""Compute the squared Euclidean distance between X and Y."""
	p1 = (a.X(), a.Y(), a.Z())
	p2 = (b.X(), b.Y(), b.Z())
	return sum((i-j)**2 for i, j in zip(p1, p2))

BT = collections.namedtuple("BT", ["value", "left", "right"])
BT.__doc__ = """
A Binary Tree (BT) with a node value, and left- and
right-subtrees.
"""
def firstItem(face):
	#v = topologic.FaceUtility.VertexAtParameters(face, 0.5, 0.5)
	v = face.Centroid()
	return v.X()
def secondItem(face):
	#v = topologic.FaceUtility.VertexAtParameters(face, 0.5, 0.5)
	v = face.Centroid()
	return v.Y()
def thirdItem(face):
	v = topologic.FaceUtility.VertexAtParameters(face, 0.5, 0.5)
	v = face.Centroid()
	return v.Z()

def itemAtIndex(v, index):
	if index == 0:
		return v.X()
	elif index == 1:
		return v.Y()
	elif index == 2:
		return v.Z()

def sortList(faces, index):
	if index == 0:
		faces.sort(key=firstItem)
	elif index == 1:
		faces.sort(key=secondItem)
	elif index == 2:
		faces.sort(key=thirdItem)
	return faces

def kdtree(faces):
	"""Construct a k-d tree from an iterable of faces.

    This algorithm is taken from Wikipedia. For more details,

    > https://en.wikipedia.org/wiki/K-d_tree#Construction

    """
	# k = len(points[0])
	k = 3

	def build(*, faces, depth):
		if len(faces) == 0:
			return None
		#points.sort(key=operator.itemgetter(depth % k))
		faces = sortList(faces, (depth % k))

		middle = len(faces) // 2
		
		return BT(
			value = faces[middle],
			left = build(
				faces=faces[:middle],
				depth=depth+1,
			),
			right = build(
				faces=faces[middle+1:],
				depth=depth+1,
			),
		)

	return build(faces=list(faces), depth=0)

NNRecord = collections.namedtuple("NNRecord", ["point", "distance"])
NNRecord.__doc__ = """
Used to keep track of the current best guess during a nearest
neighbor search.
"""

def find_nearest_neighbor(*, tree, point):
	"""Find the nearest neighbor in a k-d tree for a given
	point.
	"""
	#k = len(point)
	k = 3 # Forcing k to be 3 dimensional
	best = None
	def search(*, tree, depth):
		"""Recursively search through the k-d tree to find the
		nearest neighbor.
		"""
		nonlocal best

		if tree is None:
			return
		#treePoint = topologic.FaceUtility.VertexAtParameters(tree.value, 0.5, 0.5)
		treePoint = tree.value.Centroid()
		distance = SED(treePoint, point) topologic.VertexUtility.Distance(point, tree.value)
		if best is None or distance < best.distance:
			best = NNRecord(point=tree.value, distance=distance)

		axis = depth % k
		diff = itemAtIndex(point,axis) - itemAtIndex(treePoint,axis)
		if diff <= 0:
			close, away = tree.left, tree.right
		else:
			close, away = tree.right, tree.left

		search(tree=close, depth=depth+1)
		if diff**2 < best.distance:
			search(tree=away, depth=depth+1)

	search(tree=tree, depth=0)
	return best.point

def processItem(input):
	vertex = input[0]
	topology = input[1]
	tolerance = input[2]
	cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
	_ = topology.Cells(cells)
	for aCell in cells:
		if (topologic.CellUtility.Contains(aCell, vertex, tolerance) == 0):
			return aCell
	return None

def processItemKDTree(input):
	vertex = input[0]
	topology = input[1]
	tolerance = input[2]
	faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	_ = topology.Faces(faces)
	tree = kdtree(faces)
	nearestFace = find_nearest_neighbor(tree=tree, point=vertex)
	cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
	_ = nearestFace.Cells(cells)
	for aCell in cells:
		if (topologic.CellUtility.Contains(aCell, vertex, tolerance) == 0):
			return aCell
	return list(cells)

class SvVertexEnclosingCell(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Finds the enclosing Cell of the input Vertex within the input Topology
	"""
	bl_idname = 'SvVertexEnclosingCell'
	bl_label = 'Vertex.EnclosingCell'
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)
	UseKDTree: BoolProperty(name="UseKDTree", default=False, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.inputs.new('SvStringsSocket', 'Use k-d Tree').prop_name = 'UseKDTree'
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		vertexList = self.inputs['Vertex'].sv_get(deepcopy=False)
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=False)[0]
		useKDTreeList = self.inputs['Use k-d Tree'].sv_get(deepcopy=False)[0]
		matchLengths([vertexList, topologyList, toleranceList, useKDTreeList])
		inputs = zip(vertexList, topologyList, toleranceList, useKDTreeList)
		outputs = []
		for anInput in inputs:
			useKDTree = anInput[3]
			if useKDTree == True:
				outputs.append(processItemKDTree(anInput))
			else:
				outputs.append(processItem(anInput))
		self.outputs['Cell'].sv_set(outputs)
		end = time.time()
		print("Enclosing Cell Operation consumed "+str(round(end - start,2))+" seconds")

def register():
	bpy.utils.register_class(SvVertexEnclosingCell)

def unregister():
	bpy.utils.unregister_class(SvVertexEnclosingCell)
