#This code is contributed by Neelam Yadav 
import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import time
from collections import defaultdict

#Class to represent a graph 
class Graph: 

	def __init__(self,vertices): 
		self.V= vertices #No. of vertices 
		self.graph = [] # default dictionary 
								# to store graph 
		

	# function to add an edge to graph 
	def addEdge(self,u,v,w): 
		self.graph.append([u,v,w]) 

	# A utility function to find set of an element i 
	# (uses path compression technique) 
	def find(self, parent, i): 
		if parent[i] == i: 
			return i 
		return self.find(parent, parent[i]) 

	# A function that does union of two sets of x and y 
	# (uses union by rank) 
	def union(self, parent, rank, x, y): 
		xroot = self.find(parent, x) 
		yroot = self.find(parent, y) 

		# Attach smaller rank tree under root of 
		# high rank tree (Union by Rank) 
		if rank[xroot] < rank[yroot]: 
			parent[xroot] = yroot 
		elif rank[xroot] > rank[yroot]: 
			parent[yroot] = xroot 

		# If ranks are same, then make one as root 
		# and increment its rank by one 
		else : 
			parent[yroot] = xroot 
			rank[xroot] += 1

	# The main function to construct MST using Kruskal's 
		# algorithm 
	def KruskalMST(self): 

		result =[] #This will store the resultant MST 

		i = 0 # An index variable, used for sorted edges 
		e = 0 # An index variable, used for result[] 

			# Step 1: Sort all the edges in non-decreasing 
				# order of their 
				# weight. If we are not allowed to change the 
				# given graph, we can create a copy of graph 
		self.graph = sorted(self.graph,key=lambda item: item[2]) 

		parent = [] ; rank = [] 

		# Create V subsets with single elements 
		for node in range(self.V): 
			parent.append(node) 
			rank.append(0) 
	
		# Number of edges to be taken is equal to V-1 
		while e < self.V -1 : 

			# Step 2: Pick the smallest edge and increment 
					# the index for next iteration 
			u,v,w = self.graph[i] 
			i = i + 1
			x = self.find(parent, u) 
			y = self.find(parent ,v) 

			# If including this edge doesn't cause cycle, 
						# include it in result and increment the index 
						# of result for next edge 
			if x != y: 
				e = e + 1	
				result.append([u,v,w]) 
				self.union(parent, rank, x, y)			 
			# Else discard the edge 

		# print the contents of result[] to display the built MST 
		return result

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def repeat(list):
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

# From https://stackoverflow.com/questions/34432056/repeat-elements-of-list-between-each-other-until-we-reach-a-certain-length
def onestep(cur,y,base):
    # one step of the iteration
    if cur is not None:
        y.append(cur)
        base.append(cur)
    else:
        y.append(base[0])  # append is simplest, for now
        base = base[1:]+[base[0]]  # rotate
    return base

def iterate(list):
	maxLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		for i in range(len(anItem), maxLength):
			anItem.append(None)
		y=[]
		base=[]
		for cur in anItem:
			base = onestep(cur,y,base)
		returnList.append(y)
	return returnList

def trim(list):
	minLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength < minLength:
			minLength = newLength
	for anItem in list:
		anItem = anItem[:minLength]
		returnList.append(anItem)
	return returnList

# Adapted from https://stackoverflow.com/questions/533905/get-the-cartesian-product-of-a-series-of-lists
def interlace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in interlace(ar_list[1:]):
                yield [a,]+prod

def transposeList(l):
	length = len(l[0])
	returnList = []
	for i in range(length):
		tempRow = []
		for j in range(len(l)):
			tempRow.append(l[j][i])
		returnList.append(tempRow)
	return returnList

def listAttributeValues(listAttribute):
	listAttributes = listAttribute.ListValue()
	returnList = []
	for attr in listAttributes:
		if isinstance(attr, IntAttribute):
			returnList.append(attr.IntValue())
		elif isinstance(attr, DoubleAttribute):
			returnList.append(attr.DoubleValue())
		elif isinstance(attr, StringAttribute):
			returnList.append(attr.StringValue())
	return returnList

def valueAtKey(item, key):
	try:
		attr = item.ValueAtKey(key)
	except:
		raise Exception("Dictionary.ValueAtKey - Error: Could not retrieve a Value at the specified key ("+key+")")
	if isinstance(attr, IntAttribute):
		return (attr.IntValue())
	elif isinstance(attr, DoubleAttribute):
		return (attr.DoubleValue())
	elif isinstance(attr, StringAttribute):
		return (attr.StringValue())
	elif isinstance(attr, ListAttribute):
		return (listAttributeValues(attr))
	else:
		return None

def vertexIndex(v, vertices, tolerance):
	i = 0
	for aVertex in vertices:
		if topologic.VertexUtility.Distance(v, aVertex) < tolerance:
			return i
		i = i + 1
	return None

def processItem(item):
	#This code is contributed by Neelam Yadav 
	graph = item[0]
	edgeKey = item[1]
	tolerance = item[2]
	vertices = []
	_ = graph.Vertices(vertices)
	edges = []
	_ = graph.Edges(vertices, tolerance, edges)
	g = Graph(len(vertices))
	for anEdge in edges:
		sv = anEdge.StartVertex()
		svi = vertexIndex(sv, vertices, tolerance)
		ev = anEdge.EndVertex()
		evi = vertexIndex(ev, vertices, tolerance)
		edgeDict = anEdge.GetDictionary()
		weight = 1
		if (edgeDict):
			try:
				weight = valueAtKey(edgeDict,edgeKey)
			except:
				weight = 1
		g.addEdge(svi, evi, weight) 

	graphEdges = g.KruskalMST() # Get the Minimum Spanning Tree
	# Create an initial Topologic Graph with one Vertex
	sv = vertices[graphEdges[0][0]]
	finalGraph = topologic.Graph.ByTopology(sv, True, False, False, False, False, False, tolerance)
	stl_keys = []
	stl_keys.append(edgeKey)

	eedges = []
	for i in range(len(graphEdges)):
		sv = vertices[graphEdges[i][0]]
		ev = vertices[graphEdges[i][1]]
		tEdge = topologic.Edge.ByStartVertexEndVertex(sv, ev)
		dictValue = graphEdges[i][2]
		stl_values = []
		stl_values.append(topologic.DoubleAttribute(dictValue))
		edgeDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
		_ = tEdge.SetDictionary(edgeDict)
		eedges.append(tEdge)
	finalGraph.AddEdges(eedges, tolerance)
	return finalGraph


replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvGraphMST(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Minimum Spanning Tree (MST) of the input Graph
	"""
	bl_idname = 'SvGraphMST'
	bl_label = 'Graph.MST'
	EdgeKey: StringProperty(name='EdgeKey', update=updateNode)
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Edge Key').prop_name='EdgeKey'
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'MST')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		graphList = self.inputs['Graph'].sv_get(deepcopy=True)
		edgeKeyList = self.inputs['Edge Key'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tol'].sv_get(deepcopy=True)
		graphList = flatten(graphList)
		edgeKeyList = flatten(edgeKeyList)
		if edgeKeyList == []:
			edgeKeyList = ["Length"]
		toleranceList = flatten(toleranceList)
		inputs = [graphList, edgeKeyList, toleranceList]
		outputs = []
		if ((self.Replication) == "Default"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['MST'].sv_set(outputs)
		end = time.time()
		print("Graph.MST Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphMST)

def unregister():
    bpy.utils.unregister_class(SvGraphMST)
