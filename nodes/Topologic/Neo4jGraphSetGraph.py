import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic
import time
try:
	import py2neo
except:
	raise Exception("Error: Could not import py2neo.")

from py2neo import Node,Relationship,Graph,Path,Subgraph
from py2neo import NodeMatcher,RelationshipMatcher
from py2neo.data import spatial as sp

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

def getKeysAndValues(item):
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
	return [keys,returnList]

def vertexIndex(v, vertexList, tolerance):
	for i in range(len(vertexList)):
		d = topologic.VertexUtility.Distance(v, vertexList[i])
		if d < tolerance:
			return i
	return None

def getValueAtKey(d, searchString):
	keys, values = getKeysAndValues(d)
	for i in range(len(keys)):
		if keys[i].lower() == searchString.lower():
			return values[i]
	return None

def processItem(item):
	neo4jGraph, topologicGraph, labelKey, relationshipKey, bidirectional, deleteAll, tolerance, run = item
	if not (run):
		return None
	import time
	gmt = time.gmtime()
	timestamp =  str(gmt.tm_zone)+"_"+str(gmt.tm_year)+"_"+str(gmt.tm_mon)+"_"+str(gmt.tm_wday)+"_"+str(gmt.tm_hour)+"_"+str(gmt.tm_min)+"_"+str(gmt.tm_sec)

	vertices = []
	_ = topologicGraph.Vertices(vertices)
	edges = []
	_ = topologicGraph.Edges(edges)
	notUsed = []
	tx = neo4jGraph.begin()
	nodes = []
	for  i in range(len(vertices)):
		vDict = vertices[i].GetDictionary()
		keys, values = getKeysAndValues(vDict)
		keys.append("x")
		keys.append("y")
		keys.append("z")
		keys.append("timestamp")
		keys.append("location")
		values.append(vertices[i].X())
		values.append(vertices[i].Y())
		values.append(vertices[i].Z())
		values.append(timestamp)
		values.append(sp.CartesianPoint([vertices[i].X(),vertices[i].Y(),vertices[i].Z()]))
		zip_iterator = zip(keys, values)
		pydict = dict(zip_iterator)
		if (labelKey == 'None') or (not (labelKey)):
			nodeName = "TopologicGraphVertex"
		else:
			nodeName = str(getValueAtKey(vDict, labelKey))
		n = py2neo.Node(nodeName, **pydict)
		tx.create(n)
		nodes.append(n)
	for i in range(len(edges)):
		e = edges[i]
		sv = e.StartVertex()
		ev = e.EndVertex()
		sn = nodes[vertexIndex(sv, vertices, tolerance)]
		en = nodes[vertexIndex(ev, vertices, tolerance)]
		ed = e.GetDictionary()
		relationshipType = getValueAtKey(ed, relationshipKey)
		if not (relationshipType):
			relationshipType = "Connected To"
		snen = py2neo.Relationship(sn, relationshipType, en)
		tx.create(snen)
		if bidirectional:
			snen = py2neo.Relationship(en, relationshipType, sn)
			tx.create(snen)
	if deleteAll:
		neo4jGraph.delete_all()
	neo4jGraph.commit(tx)
	return neo4jGraph

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvNeo4jGraphSetGraph(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Sets the input Topologic Graph to the input Neo4j Graph. This will delete all previous remote graphs. 
	"""
	bl_idname = 'SvNeo4jGraphSetGraph'
	bl_label = 'Neo4jGraph.SetGraph'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=0, precision=4, update=updateNode)
	labelKey: StringProperty(name="Label Key", default="None", update=updateNode)
	relationshipKey: StringProperty(name="Relationship Type Key", default="relationship", update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, min=0, precision=4, update=updateNode)
	Run: BoolProperty(name="Run", default=True, update=updateNode)
	Bidirectional: BoolProperty(name="Bidirectional", default=True, update=updateNode)
	DeleteAll: BoolProperty(name="Delete Previous Graphs", default=True, update=updateNode)

	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		#self.inputs[0].label = 'Auto'
		self.inputs.new('SvStringsSocket', 'Neo4j Graph')
		self.inputs.new('SvStringsSocket', 'Topologic Graph')
		self.inputs.new('SvStringsSocket', 'Label Key').prop_name='labelKey'
		self.inputs.new('SvStringsSocket', 'Relationship Key').prop_name='relationshipKey'
		self.inputs.new('SvStringsSocket', 'Bidirectional').prop_name = 'Bidirectional'
		self.inputs.new('SvStringsSocket', 'DeleteAll').prop_name = 'DeleteAll'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.inputs.new('SvStringsSocket', 'Run').prop_name = 'Run'
		self.outputs.new('SvStringsSocket', 'Neo4j Graph')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not (self.inputs['Neo4j Graph'].is_linked):
			return
		if not (self.inputs['Topologic Graph'].is_linked):
			return
		neo4jGraphList = self.inputs['Neo4j Graph'].sv_get(deepcopy=True)
		topologicGraphList = self.inputs['Topologic Graph'].sv_get(deepcopy=True)
		labelKeyList = self.inputs['Label Key'].sv_get(deepcopy=True)
		relationshipKeyList = self.inputs['Relationship Key'].sv_get(deepcopy=True)
		bidirectionalList = self.inputs['Bidirectional'].sv_get(deepcopy=True)
		deleteAllList = self.inputs['DeleteAll'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		runList = self.inputs['Run'].sv_get(deepcopy=True)
		neo4jGraphList = flatten(neo4jGraphList)
		topologicGraphList = flatten(topologicGraphList)
		labelKeyList = flatten(labelKeyList)
		relationshipKeyList = flatten(relationshipKeyList)
		bidirectionalList = flatten(bidirectionalList)
		deleteAllList = flatten(deleteAllList)
		toleranceList = flatten(toleranceList)
		runList = flatten(runList)
		inputs = [neo4jGraphList, topologicGraphList, labelKeyList, relationshipKeyList, bidirectionalList, deleteAllList, toleranceList, runList]
		if ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Default") or ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Neo4j Graph'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvNeo4jGraphSetGraph)

def unregister():
    bpy.utils.unregister_class(SvNeo4jGraphSetGraph)
