import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
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
		if isinstance(attr, topologic.IntAttribute):
			returnList.append(attr.IntValue())
		elif isinstance(attr, topologic.DoubleAttribute):
			returnList.append(attr.DoubleValue())
		elif isinstance(attr, topologic.StringAttribute):
			returnList.append(attr.StringValue())
	return returnList

def getValueAtKey(item, key):
	try:
		attr = item.ValueAtKey(key)
	except:
		raise Exception("Dictionary.ValueAtKey - Error: Could not retrieve a Value at the specified key ("+key+")")
	if isinstance(attr, topologic.IntAttribute):
		return (attr.IntValue())
	elif isinstance(attr, topologic.DoubleAttribute):
		return (attr.DoubleValue())
	elif isinstance(attr, topologic.StringAttribute):
		return (attr.StringValue())
	elif isinstance(attr, topologic.ListAttribute):
		return (listAttributeValues(attr))
	else:
		return None

def getValues(item):
	keys = item.Keys()
	returnList = []
	for key in keys:
		try:
			attr = item.ValueAtKey(key)
		except:
			raise Exception("Dictionary.Values - Error: Could not retrieve a Value at the specified key ("+key+")")
		if isinstance(attr, topologic.IntAttribute):
			returnList.append(attr.IntValue())
		elif isinstance(attr, topologic.DoubleAttribute):
			returnList.append(attr.DoubleValue())
		elif isinstance(attr, topologic.StringAttribute):
			returnList.append(attr.StringValue())
		elif isinstance(attr, topologic.ListAttribute):
			returnList.append(listAttributeValues(attr))
		else:
			returnList.append("")
	return returnList

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("DictionaryByKeysValues - Keys and Values do not have the same length")
	stl_keys = []
	stl_values = []
	for i in range(len(keys)):
		if isinstance(keys[i], str):
			stl_keys.append(keys[i])
		else:
			stl_keys.append(str(keys[i]))
		if isinstance(values[i], list) and len(values[i]) == 1:
			value = values[i][0]
		else:
			value = values[i]
		if isinstance(value, bool):
			if value == False:
				stl_values.append(topologic.IntAttribute(0))
			else:
				stl_values.append(topologic.IntAttribute(1))
		elif isinstance(value, int):
			stl_values.append(topologic.IntAttribute(value))
		elif isinstance(value, float):
			stl_values.append(topologic.DoubleAttribute(value))
		elif isinstance(value, str):
			stl_values.append(topologic.StringAttribute(value))
		elif isinstance(value, list):
			l = []
			for v in value:
				if isinstance(v, bool):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, int):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, float):
					l.append(topologic.DoubleAttribute(v))
				elif isinstance(v, str):
					l.append(topologic.StringAttribute(v))
			stl_values.append(topologic.ListAttribute(l))
		else:
			raise Exception("Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
	myDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
	return myDict

def mergeDictionaries(sources):
	sinkKeys = []
	sinkValues = []
	d = sources[0]
	if d != None:
		stlKeys = d.Keys()
		if len(stlKeys) > 0:
			sinkKeys = d.Keys()
			sinkValues = getValues(d)
		for i in range(1,len(sources)):
			d = sources[i]
			if d == None:
				continue
			stlKeys = d.Keys()
			if len(stlKeys) > 0:
				sourceKeys = d.Keys()
				for aSourceKey in sourceKeys:
					if aSourceKey not in sinkKeys:
						sinkKeys.append(aSourceKey)
						sinkValues.append("")
				for i in range(len(sourceKeys)):
					index = sinkKeys.index(sourceKeys[i])
					sourceValue = getValueAtKey(d,sourceKeys[i])
					if sourceValue != None:
						if sinkValues[index] != "":
							if isinstance(sinkValues[index], list):
								sinkValues[index].append(sourceValue)
							else:
								sinkValues[index] = [sinkValues[index], sourceValue]
						else:
							sinkValues[index] = sourceValue
	if len(sinkKeys) > 0 and len(sinkValues) > 0:
		newDict = processKeysValues(sinkKeys, sinkValues)
		return newDict
	return None

def addIfUnique(graph_vertices, vertex, tolerance):
	unique = True
	returnVertex = vertex
	for gv in graph_vertices:
		if (topologic.VertexUtility.Distance(vertex, gv) < tolerance):
			gd = gv.GetDictionary()
			vd = vertex.GetDictionary()
			gk = gd.Keys()
			vk = vd.Keys()
			d = None
			if (len(gk) > 0) and (len(vk) > 0):
				d = mergeDictionaries([gd, vd])
			elif (len(gk) > 0) and (len(vk) < 1):
				d = gd
			elif (len(gk) < 1) and (len(vk) > 0):
				d = vd
			if d:
				_ = gv.SetDictionary(d)
			unique = False
			returnVertex = gv
			break
	if unique:
		graph_vertices.append(vertex)
	return [graph_vertices, returnVertex]

def processItem(item):
	graph = item[0]
	edges = item[1]
	tolerance = item[2]
	graph_edges = []
	graph_vertices = []
	if graph:
		_ = graph.Vertices(graph_vertices)
		_ = graph.Edges(graph_vertices, tolerance, graph_edges)
	if edges:
		if isinstance(edges, list) == False:
			edges = [edges]
		for edge in edges:
			vertices = []
			_ = edge.Vertices(None, vertices)
			new_vertices = []
			for vertex in vertices:
				graph_vertices, nv = addIfUnique(graph_vertices, vertex, tolerance)
				new_vertices.append(nv)
			new_edge = topologic.Edge.ByStartVertexEndVertex(new_vertices[0], new_vertices[1])
			_ = new_edge.SetDictionary(edge.GetDictionary())
			graph_edges.append(new_edge)
	new_graph = topologic.Graph.ByVerticesEdges(graph_vertices, graph_edges)
	return new_graph

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvGraphAddEdge(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Adds the input Edge to the input Graph
	"""
	bl_idname = 'SvGraphAddEdge'
	bl_label = 'Graph.AddEdge'
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Edge')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Graph')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		graphList = self.inputs['Graph'].sv_get(deepcopy=True)
		edgeList = self.inputs['Edge'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		graphList = flatten(graphList)
		toleranceList = flatten(toleranceList)
		inputs = [graphList, edgeList, toleranceList]
		outputs = []
		if ((self.Replication) == "Default"):
			edgeList = flatten(edgeList)
			outputs = processItem([graphList[0], edgeList, toleranceList[0]])
			self.outputs['Graph'].sv_set([outputs])
			end = time.time()
			print("Graph Add Edge Operation consumed "+str(round(end - start,4))+" seconds")
			return
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
		self.outputs['Graph'].sv_set(outputs)
		end = time.time()
		print("Graph Add Edge Operation consumed "+str(round(end - start,4))+" seconds")
def register():
    bpy.utils.register_class(SvGraphAddEdge)

def unregister():
    bpy.utils.unregister_class(SvGraphAddEdge)
