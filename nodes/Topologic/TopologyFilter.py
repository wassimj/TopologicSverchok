import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import re

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

def listToString(item):
	returnString = ""
	if isinstance(item, list):
		if len(item) < 2:
			return str(item[0])
		else:
			returnString = item[0]
			for i in range(1, len(item)):
				returnString = returnString+str(item[i])
	return returnString

def valueAtKey(item, key):
	try:
		attr = item.ValueAtKey(key)
	except:
		raise Exception("Dictionary.ValueAtKey - Error: Could not retrieve a Value at the specified key ("+key+")")
	if isinstance(attr, topologic.IntAttribute):
		return str(attr.IntValue())
	elif isinstance(attr, topologic.DoubleAttribute):
		return str(attr.DoubleValue())
	elif isinstance(attr, topologic.StringAttribute):
		return (attr.StringValue())
	elif isinstance(attr, topologic.ListAttribute):
		return listToString(listAttributeValues(attr))
	else:
		return None

def processItem(topologies, topologyType, searchType, item):
	key = item[0]
	value = item[1]
	filteredTopologies = []
	otherTopologies = []
	for aTopology in topologies:
		if not aTopology:
			continue
		if (topologyType == "Any") or (aTopology.GetTypeAsString() == topologyType):
			if value == "" or key == "":
				filteredTopologies.append(aTopology)
			else:
				if isinstance(value, list):
					value.sort()
					value = str(value)
				value.replace("*",".+")
				value = value.lower()
				d = aTopology.GetDictionary()
				v = valueAtKey(d, key)
				if v != None:
					v = v.lower()
					if searchType == "Equal To":
						searchResult = (value == v)
					elif searchType == "Contains":
						searchResult = (value in v)
					elif searchType == "Starts With":
						searchResult = (value == v[0: len(value)])
					elif searchType == "Ends With":
						searchResult = (value == v[len(v)-len(value):len(v)])
					elif searchType == "Not Equal To":
						searchResult = not (value == v)
					elif searchType == "Does Not Contain":
						searchResult = not (value in v)
					else:
						searchResult = False
					if searchResult:
						filteredTopologies.append(aTopology)
					else:
						otherTopologies.append(aTopology)
				else:
					otherTopologies.append(aTopology)
		else:
			otherTopologies.append(aTopology)
	return [filteredTopologies, otherTopologies]

topologyTypes = [("Any", "Any", "", 1),("Vertex", "Vertex", "", 2),("Edge", "Edge", "", 3),("Wire", "Wire", "", 4),("Face", "Face", "", 5),("Shell", "Shell", "", 6), ("Cell", "Cell", "", 7),("CellComplex", "CellComplex", "", 8), ("Cluster", "Cluster", "", 9)]
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
searchType = [("Equal To", "Equal To", "", 1),("Contains", "Contains", "", 2),("Starts With", "Starts With", "", 3),("Ends With", "Ends With", "", 4),("Not Equal To", "Not Equal To", "", 5),("Does Not Contain", "Does Not Contain", "", 6)]

class SvTopologyFilter(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Filters the input list of Topologies based on the input Topology type filter    
	"""
	bl_idname = 'SvTopologyFilter'
	bl_label = 'Topology.Filter'
	TopologyType: EnumProperty(name="Topology Type", description="Specify topology type", default="Any", items=topologyTypes, update=updateNode)
	Key: StringProperty(name='Key', update=updateNode)
	Value: StringProperty(name='Value', update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	SearchType: EnumProperty(name="Search Type", description="Search Type", default="Equal To", items=searchType, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topologies')
		self.inputs.new('SvStringsSocket', 'Key').prop_name='Key'
		self.inputs.new('SvStringsSocket', 'Value').prop_name='Value'
		self.outputs.new('SvStringsSocket', 'Filtered Topologies')
		self.outputs.new('SvStringsSocket', 'Other Topologies')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "TopologyType",text="")
		layout.prop(self, "SearchType",text="")


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Filtered Topologies'].sv_set([])
			self.outputs['Other Topologies'].sv_set([])
			return
		inputs = self.inputs['Topologies'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		topologyList = self.inputs['Topologies'].sv_get(deepcopy=True)
		keyList = self.inputs['Key'].sv_get(deepcopy=True)
		valueList = self.inputs['Value'].sv_get(deepcopy=True)
		topologyList = flatten(topologyList)
		keyList = flatten(keyList)
		valueList = flatten(valueList)
		inputs = [keyList, valueList]
		filteredTopologies = []
		otherTopologies = []
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
			output = processItem(topologyList, self.TopologyType, self.SearchType, anInput)
			if output:
				filteredTopologies.append(output[0])
				otherTopologies.append(output[1])
		self.outputs['Filtered Topologies'].sv_set(filteredTopologies)
		self.outputs['Other Topologies'].sv_set(otherTopologies)

def register():
	bpy.utils.register_class(SvTopologyFilter)

def unregister():
	bpy.utils.unregister_class(SvTopologyFilter)
