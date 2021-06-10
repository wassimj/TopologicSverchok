import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
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

def getKeysAndValues(item):
	stl_keys = item.Keys()
	keys = []
	values = []
	copyKeys = stl_keys.__class__(stl_keys) #wlav suggested workaround. Make a copy first
	for x in copyKeys:
		k = x.c_str()
		keys.append(k)
	for key in keys:
		fv = None
		try:
			v = item.ValueAtKey(key).Value()
		except:
			raise Exception("Error: Could not retrieve a Value at the specified key ("+key+")")
		if (isinstance(v, int) or (isinstance(v, float))):
			fv = v
		elif (isinstance(v, cppyy.gbl.std.string)):
			fv = v.c_str()
		else:
			tempList = []
			for i in v:
				if isinstance(i.Value(), cppyy.gbl.std.string):
					tempList.append(i.Value().c_str())
				else:
					tempList.append(i.Value())
			fv = tempList
		values.append(fv)
	return [keys, values]

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("Keys and Values do not have the same length")
	stl_keys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
	stl_values = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
	for i in range(len(keys)):
		stl_keys.push_back(keys[i])
		if isinstance(values[i], list) and len(values[i]) == 1:
			value = values[i][0]
		else:
			value = values[i]
		if isinstance(value, bool):
			if value == False:
				stl_values.push_back(topologic.IntAttribute(0))
			else:
				stl_values.push_back(topologic.IntAttribute(1))
		elif isinstance(value, int):
			stl_values.push_back(topologic.IntAttribute(value))
		elif isinstance(value, float):
			stl_values.push_back(topologic.DoubleAttribute(value))
		elif isinstance(value, str):
			stl_values.push_back(topologic.StringAttribute(value))
		elif isinstance(value, list):
			l = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
			for v in value:
				if isinstance(v, bool):
					l.push_back(topologic.IntAttribute(v))
				elif isinstance(v, int):
					l.push_back(topologic.IntAttribute(v))
				elif isinstance(v, float):
					l.push_back(topologic.DoubleAttribute(v))
				elif isinstance(v, str):
					l.push_back(topologic.StringAttribute(v))
			stl_values.push_back(topologic.ListAttribute(l))
		else:
			raise Exception("Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
	return topologic.Dictionary.ByKeysValues(stl_keys, stl_values)

def getContents(item):
	topologyContents = []
	contents = cppyy.gbl.std.list[topologic.Topology.Ptr]()
	_ = item.Contents(contents)
	for aContent in contents:
		aContent.__class__ = classByType(aContent.GetType())
		topologyContents.append(aContent)
	return topologyContents

def processItem(item):
	topology = item[0]
	tool = item[1]
	transferDictionary = item[2]
	addNestingDepth = item[3]
	try:
		_ = topology.Divide(tool, False) # Don't transfer dictionaries just yet
	except:
		raise Exception("Error: Divide operation failed.")
	nestingDepth = "1"
	keys = ["nesting_depth"]
	values = [nestingDepth]

	if not addNestingDepth and not transferDictionary:
		return topology

	contents = getContents(topology)
	for i in range(len(contents)):
		if not addNestingDepth and transferDictionary:
			parentDictionary = topology.GetDictionary()
			if parentDictionary != None:
				_ = contents[i].setDictionary(parentDictionary)
		if addNestingDepth and transferDictionary:
			parentDictionary = topology.GetDictionary()
			if parentDictionary != None:
				keys, values = getKeysAndValues(parentDictionary)
				if ("nesting_depth" in keys):
					nestingDepth = parentDictionary.ValueAtKey(key).Value().c_str
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
			_ = contents[i].setDictionary(d)
		if addNestingDepth and  not transferDictionary:
			parentDictionary = topology.GetDictionary()
			if parentDictionary != None:
				keys, values = getKeysAndValues(parentDictionary)
				if ("nesting_depth" in keys):
					nestingDepth = parentDictionary.ValueAtKey("nesting_depth").Value().c_str()
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
