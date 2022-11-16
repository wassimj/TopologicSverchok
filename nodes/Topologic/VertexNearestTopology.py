import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time
from . import Replication
from . import TopologySubTopologies

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
	return topologic.VertexUtility.Distance(a, b)

BT = collections.namedtuple("BT", ["value", "left", "right"])
BT.__doc__ = """
A Binary Tree (BT) with a node value, and left- and
right-subtrees.
"""
def firstItem(topology):
	return topology.Centroid().X()
def secondItem(topology):
	return topology.Centroid().Y()
def thirdItem(topology):
	return topology.Centroid().Z()

def itemAtIndex(topology, index):
	v = topology.Centroid()
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

def kdtree(topology, topologyType):
	subTopologies = TopologySubTopologies.processItem([topology, topologyType])
	assert (len(subTopologies) > 0), "Vertex.NearestTopology: Could not find any of subTopologies of the specified type in the input Topology"

	"""Construct a k-d tree from an iterable of subTopologies.

    This algorithm is taken from Wikipedia. For more details,

    > https://en.wikipedia.org/wiki/K-d_tree#Construction

    """
	# k = len(points[0])
	k = 3

	def build(*, subTopologies, depth):
		if len(subTopologies) == 0:
			return None
		#points.sort(key=operator.itemgetter(depth % k))
		subTopologies = sortList(subTopologies, (depth % k))

		middle = len(subTopologies) // 2
		
		return BT(
			value = subTopologies[middle],
			left = build(
				subTopologies=subTopologies[:middle],
				depth=depth+1,
			),
			right = build(
				subTopologies=subTopologies[middle+1:],
				depth=depth+1,
			),
		)

	return build(subTopologies=list(subTopologies), depth=0)

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
		distance = SED(vertex, tree.value)
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

saved_cluster = None
saved_tree = None
def processItem(input):
	vertex, cluster, useKDTree, topologyType = input
	global saved_cluster
	global saved_tree
	tree = None
	if useKDTree:
		if not saved_cluster:
			saved_cluster = cluster
			tree = kdtree(cluster, topologyType)
			saved_tree = tree
		else:
			if saved_cluster == cluster:
				tree = saved_tree
			else:
				tree = kdtree(cluster, topologyType)
				saved_tree = tree
		return find_nearest_neighbor(tree=tree, vertex=vertex)
	else:
		distances = []
		indices = []
		subTopologies = TopologySubTopologies.processItem([cluster, topologyType])
		for i in range(len(subTopologies)):
			distances.append(SED(vertex, subTopologies[i]))
			indices.append(i)
		sorted_indices = [x for _, x in sorted(zip(distances, indices))]
	return subTopologies[sorted_indices[0]]

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
topologyTypes = [("Vertex", "Vertex", "", 1),("Edge", "Edge", "", 2),("Wire", "Wire", "", 3),("Face", "Face", "", 4),("Shell", "Shell", "", 5), ("Cell", "Cell", "", 6),("CellComplex", "CellComplex", "", 7), ("Cluster", "Cluster", "", 8), ("Aperture", "Aperture", "", 9)]

class SvVertexNearestTopology(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the nearest Topology to the input Vertex from the input Cluster
	"""
	bl_idname = 'SvVertexNearestTopology'
	bl_label = 'Vertex.NearestTopology'
	bl_icon = 'SELECT_DIFFERENCE'
	UseKDTree: BoolProperty(name="UseKDTree", default=False, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	TopologyType: EnumProperty(name="Topology Type", description="Specify topology type", default="Vertex", items=topologyTypes, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.inputs.new('SvStringsSocket', 'Topology Cluster')
		self.inputs.new('SvStringsSocket', 'Use k-d Tree').prop_name = 'UseKDTree'
		self.outputs.new('SvStringsSocket', 'Topology')
		self.width = 175
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "draw_sockets"

	def draw_sockets(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="Replication")
		split.row().prop(self, "Replication",text="")
		row = layout.row()
		split = row.split(factor=0.5)
		split.row().label(text="TopologyType")
		split.row().prop(self, "TopologyType",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs_nested = []
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_nested.append(inp)
			inputs_flat.append(Replication.flatten(inp))
		inputs_nested.append([self.TopologyType])
		inputs_flat.append([self.TopologyType])
		inputs_replicated = Replication.replicateInputs(inputs_flat, self.Replication)
		outputs = []
		for anInput in inputs_replicated:
			outputs.append(processItem(anInput))
		inputs_flat = []
		for anInput in self.inputs:
			inp = anInput.sv_get(deepcopy=True)
			inputs_flat.append(Replication.flatten(inp))
		inputs_flat.append([self.TopologyType])
		if self.Replication == "Interlace":
			outputs = Replication.re_interlace(outputs, inputs_flat)
		else:
			match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
			outputs = Replication.unflatten(outputs, match_list)
		if len(outputs) == 1:
			if isinstance(outputs[0], list):
				outputs = outputs[0]
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvVertexNearestTopology)

def unregister():
	bpy.utils.unregister_class(SvVertexNearestTopology)
