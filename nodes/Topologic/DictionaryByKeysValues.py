import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
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

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("Keys and Values do not have the same length")
	stl_keys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
	stl_values = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
	for i in range(len(keys)):
		stl_keys.push_back(keys[i])
		if isinstance(values[i], bool):
			if values[i] == False:
				stl_values.push_back(topologic.IntAttribute(0))
			else:
				stl_values.push_back(topologic.IntAttribute(1))
		elif isinstance(values[i], int):
			stl_values.push_back(topologic.IntAttribute(values[i]))
		elif isinstance(values[i], float):
			stl_values.push_back(topologic.DoubleAttribute(values[i]))
		elif isinstance(values[i], str):
			stl_values.push_back(topologic.StringAttribute(values[i]))
		elif isinstance(values[i], list):
			l = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
			for v in values[i]:
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

def processItem(item):
	keys = item[0]
	values = item[1]
	if isinstance(keys, list) == False:
		keys = [keys]
	if isinstance(values, list) == False:
		values = [values]
	return processKeysValues(keys, values)

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDictionaryByKeysValues(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Dictionary from a list of keys and values   
	"""
	bl_idname = 'SvDictionaryByKeysValues'
	bl_label = 'Dictionary.ByKeysValues'
	Keys: StringProperty(name="Keys", update=updateNode)
	Values: StringProperty(name="Values", update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Keys').prop_name='Keys'
		self.inputs.new('SvStringsSocket', 'Values').prop_name='Values'
		self.outputs.new('SvStringsSocket', 'Dictionary')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		keyList = self.inputs['Keys'].sv_get(deepcopy=True)
		valueList = self.inputs['Values'].sv_get(deepcopy=True)
		if len(keyList) == 1:
			keyList = flatten(keyList)
		inputs = [keyList, valueList]
		outputs = []
		if ((self.Replication) == "Default"):
			outputs.append(processKeysValues(keyList, valueList))
			self.outputs['Dictionary'].sv_set(outputs)
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
		self.outputs['Dictionary'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDictionaryByKeysValues)

def unregister():
	bpy.utils.unregister_class(SvDictionaryByKeysValues)
