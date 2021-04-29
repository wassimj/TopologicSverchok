import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import cppyy
import time

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList
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

def classByType(argument):
	switcher = {
		1: Vertex,
		2: Edge,
		4: Wire,
		8: Face,
		16: Shell,
		32: Cell,
		64: CellComplex,
		128: Cluster }
	return switcher.get(argument, Topology)

def fixTopologyClass(topology):
  topology.__class__ = classByType(topology.GetType())
  return topology

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
	"""Construct a k-d tree from an iterable of vertices.

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
		if topologic.Topology.IsSame(tree.value, vertex) == False:
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

def processItem(cells):
	print(cells)
	cellComplex = None
	# get all the internal vertices
	ivList = []
	for aCell in cells:
		ivList.append(topologic.CellUtility.InternalVertex(aCell, 0.0001))
	print(ivList)
	# Build a k-d tree
	tree = kdtree(ivList)
	result = fixTopologyClass(topologic.Topology.DeepCopy(cells[0]))
	interimResult = None
	for i in range(len(cells)):
		c1 = cells[i]
		nearestVertex = find_nearest_neighbor(tree=tree, vertex=ivList[i])
		print([nearestVertex.X(), nearestVertex.Y(), nearestVertex.Z()])
		nearestIndex = ivList.index(nearestVertex)
		nearestCell = cells[nearestIndex]
		try:
			result = fixTopologyClass(result.Merge(nearestCell, False))
			if result.Type() == topologic.CellComplex.Type():
				interimResult = topologic.Topology.DeepCopy(result)
			print(interimResult)
		except:
			print("Merge operation failed")
	print ("final Result: "+ str(result)+" Type:"+ str(result.GetTypeAsString()))
	if result.Type() != topologic.CellComplex.Type():
		print("Overall operation failed. Trying SelfMerge")
		result = result.SelfMerge()
		cellComplexes = cppyy.gbl.std.list[topologic.CellComplex.Ptr]()
		_ = result.CellComplexes(cellComplexes)
		return list(cellComplexes)
	return result

class SvCellComplexByCellsNew(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a CellComplex from the list of input Cells  
	"""
	bl_idname = 'SvCellComplexByCellsNew'
	bl_label = 'CellComplex.ByCellsNew'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cells')
		self.outputs.new('SvStringsSocket', 'CellComplex')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		cellsList = self.inputs['Cells'].sv_get(deepcopy=False)
		outputs = []
		if isinstance(cellsList[0], list) == False:
			cellsList = [cellsList]
		for cells in cellsList:
			outputs.append(processItem(cells))
		self.outputs['CellComplex'].sv_set(outputs)
		end = time.time()
		print("CellComplex.ByCells-New Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvCellComplexByCellsNew)

def unregister():
    bpy.utils.unregister_class(SvCellComplexByCellsNew)
