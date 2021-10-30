import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

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
			# print(base,y)
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

def getKeysAndValues(item):
	keys = item.Keys()
	values = []
	for key in keys:
		value = getValueAtKey(item, key)
		values.append(value)
	return [keys, values]

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("TopologyDivide - Error: Keys and Values do not have the same length")
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
			raise Exception("TopologyDivide - Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
	myDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
	return myDict

def processItem(item):
	topology = item[0]
	tool = item[1]
	transferDictionary = item[2]
	addNestingDepth = item[3]
	try:
		_ = topology.Divide(tool, False) # Don't transfer dictionaries just yet
	except:
		raise Exception("TopologyDivide - Error: Divide operation failed.")
	nestingDepth = "1"
	keys = ["nesting_depth"]
	values = [nestingDepth]

	if not addNestingDepth and not transferDictionary:
		return topology

	contents = []
	_ = topology.Contents(contents)
	for i in range(len(contents)):
		if not addNestingDepth and transferDictionary:
			parentDictionary = topology.GetDictionary()
			if parentDictionary != None:
				_ = contents[i].SetDictionary(parentDictionary)
		if addNestingDepth and transferDictionary:
			parentDictionary = topology.GetDictionary()
			if parentDictionary != None:
				keys, values = getKeysAndValues(parentDictionary)
				if ("nesting_depth" in keys):
					nestingDepth = parentDictionary.ValueAtKey("nesting_depth").StringValue()
				else:
					keys.append("nesting_depth")
					values.append(nestingDepth)
				parentDictionary = processKeysValues(keys, values)
			else:
				keys = ["nesting_depth"]
				values = [nestingDepth]
			parentDictionary = processKeysValues(keys, values)
			_ = topology.SetDictionary(parentDictionary)
			values[keys.index("nesting_depth")] = nestingDepth+"_"+str(i+1)
			d = processKeysValues(keys, values)
			_ = contents[i].SetDictionary(d)
		if addNestingDepth and  not transferDictionary:
			parentDictionary = topology.GetDictionary()
			if parentDictionary != None:
				keys, values = getKeysAndValues(parentDictionary)
				if ("nesting_depth" in keys):
					nestingDepth = parentDictionary.ValueAtKey("nesting_depth").StringValue()
				else:
					keys.append("nesting_depth")
					values.append(nestingDepth)
				parentDictionary = processKeysValues(keys, values)
			else:
				keys = ["nesting_depth"]
				values = [nestingDepth]
			parentDictionary = processKeysValues(keys, values)
			_ = topology.SetDictionary(parentDictionary)
			keys = ["nesting_depth"]
			v = nestingDepth+"_"+str(i+1)
			values = [v]
			d = processKeysValues(keys, values)
			_ = contents[i].SetDictionary(d)
	return topology

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]


class SvTopologyDivide(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Divide the input Topology using the input Tool and place the result in its Contents   
	"""
	bl_idname = 'SvTopologyDivide'
	bl_label = 'Topology.Divide'
	TransferDictionary: BoolProperty(name="Transfer Dictionary", default=False, update=updateNode)
	AddNestingDepth: BoolProperty(name="Add Nesting Depth", default=False, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Tool')
		self.inputs.new('SvStringsSocket', 'Transfer Dictionary').prop_name = 'TransferDictionary'
		self.inputs.new('SvStringsSocket', 'Nesting Depth').prop_name = 'AddNestingDepth'
		self.outputs.new('SvStringsSocket', 'Topology')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return

		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		toolList = self.inputs['Tool'].sv_get(deepcopy=True)
		tranDictList = self.inputs['Transfer Dictionary'].sv_get(deepcopy=True)
		addNestingDepthList = self.inputs['Nesting Depth'].sv_get(deepcopy=True)
		topologyList = flatten(topologyList)
		toolList = flatten(toolList)
		tranDictList = flatten(tranDictList)
		addNestingDepthList = flatten(addNestingDepthList)
		inputs = [topologyList, toolList, tranDictList, addNestingDepthList]
		if ((self.Replication) == "Trim"):
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
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvTopologyDivide)

def unregister():
    bpy.utils.unregister_class(SvTopologyDivide)
