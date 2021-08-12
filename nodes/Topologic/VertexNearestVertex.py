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
def firstItem(v):
	return v.X()
def secondItem(v):
	return v.Y()
def thirdItem(v):
	return v.Z()

def itemAtIndex(v, index):
	if index == 0:
		return v.X()
	elif index == 1:
		return v.Y()
	elif index == 2:
		return v.Z()

def sortList(vertices, index):
	if index == 0:
		vertices.sort(key=firstItem)
	elif index == 1:
		vertices.sort(key=secondItem)
	elif index == 2:
		vertices.sort(key=thirdItem)
	return vertices

def kdtree(vertices):
	"""Construct a k-d tree from an iterable of faces.

    This algorithm is taken from Wikipedia. For more details,

    > https://en.wikipedia.org/wiki/K-d_tree#Construction

    """
	# k = len(points[0])
	k = 3

	def build(*, vertices, depth):
		if len(vertices) == 0:
			return None
		#points.sort(key=operator.itemgetter(depth % k))
		vertices = sortList(vertices, (depth % k))

		middle = len(vertices) // 2
		
		return BT(
			value = vertices[middle],
			left = build(
				vertices=vertices[:middle],
				depth=depth+1,
			),
			right = build(
				vertices=vertices[middle+1:],
				depth=depth+1,
			),
		)

	return build(vertices=list(vertices), depth=0)

NNRecord = collections.namedtuple("NNRecord", ["vertex", "distance"])
NNRecord.__doc__ = """
Used to keep track of the current best guess during a nearest
neighbor search.
"""

def find_nearest_neighbor(*, tree, vertex):
	"""Find the nearest neighbor in a k-d tree for a given vertex.
	"""
	k = 3 # Forcing k to be 3 dimensional
	best = None
	def search(*, tree, depth):
		"""Recursively search through the k-d tree to find the nearest neighbor.
		"""
		nonlocal best

		if tree is None:
			return
		distance = SED(tree.value, vertex)
		if best is None or distance < best.distance:
			best = NNRecord(vertex=tree.value, distance=distance)

		axis = depth % k
		diff = itemAtIndex(vertex,axis) - itemAtIndex(tree.value,axis)
		if diff <= 0:
			close, away = tree.left, tree.right
		else:
			close, away = tree.right, tree.left

		search(tree=close, depth=depth+1)
		if diff**2 < best.distance:
			search(tree=away, depth=depth+1)

	search(tree=tree, depth=0)
	return best.vertex

def processItem(input):
	vertex = input[0]
	vertices = input[1]
	minDistance = SED(vertex, vertices[0])
	nearestVertex = vertices[0]
	for v in vertices:
		d = SED(vertex, v)
		if d < minDistance:
			minDistance = d
			nearestVertex = v
	return nearestVertex

def processItemKDTree(input):
	return find_nearest_neighbor(tree=input[1], vertex=input[0])

class SvVertexNearestVertex(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the nearest Vertex to the input Vertex from the list of input Vertices
	"""
	bl_idname = 'SvVertexNearestVertex'
	bl_label = 'Vertex.NearestVertex'
	UseKDTree: BoolProperty(name="UseKDTree", default=False, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.inputs.new('SvStringsSocket', 'Vertices')
		self.inputs.new('SvStringsSocket', 'Use k-d Tree').prop_name = 'UseKDTree'
		self.outputs.new('SvStringsSocket', 'Vertex')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		vertexList = self.inputs['Vertex'].sv_get(deepcopy=True)
		verticesList = self.inputs['Vertices'].sv_get(deepcopy=True)
		useKDTreeList = self.inputs['Use k-d Tree'].sv_get(deepcopy=True)[0]
		if verticesList:
			if isinstance(verticesList[0], list) == False:
				verticesList = [verticesList]
		outputs = []
		trees = []
		for i in range(len(verticesList)):
			if useKDTreeList[i] == True:
				trees.append(kdtree(verticesList[i]))
			else:
				trees.append(verticesList[i])
		matchLengths([vertexList, trees, useKDTreeList])
		inputs = zip(vertexList, trees, useKDTreeList)
		for anInput in inputs:
			useKDTree = anInput[2]
			if useKDTree == True:
				outputs.append(processItemKDTree(anInput))
			else:
				outputs.append(processItem(anInput))
		end = time.time()
		print("Use k-d tree: "+str(useKDTree)+". Nearest Vertex Operation consumed "+str(round(end - start,4))+" seconds")
		self.outputs['Vertex'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvVertexNearestVertex)

def unregister():
	bpy.utils.unregister_class(SvVertexNearestVertex)
