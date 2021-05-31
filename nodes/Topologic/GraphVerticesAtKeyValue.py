import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
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

def processItem(item):
	vertex = item[0]
	key = item[1]
	value = item[2]
	fv = None
	if isinstance(value, list):
		value.sort()
	try:
		d = vertex.GetDictionary()
		v = d.ValueAtKey(key).Value()
	except:
		print("Failed to find the Key and Value")
		return None
	if (isinstance(v, int) or (isinstance(v, float))):
		fv = v
	elif (isinstance(v, cppyy.gbl.std.string)):
		fv = v.c_str()
	else:
		resultList = []
		for i in v:
			if isinstance(i.Value(), cppyy.gbl.std.string):
				resultList.append(i.Value().c_str())
			else:
				resultList.append(i.Value())
		fv = resultList.sort()

	print("Value is: "+str(fv))
	print("Comparing to: "+str(value))
	if str(fv) == str(value):
		print("Success!!")
		return vertex
	else:
		print("Failure!!")
	return None

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvGraphVerticesAtKeyValue(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Vertices that have the input Value at the input Key
	"""
	bl_idname = 'SvGraphVerticesAtKeyValue'
	bl_label = 'Graph.VerticesAtKeyValue'
	Key: StringProperty(name='Key', update=updateNode)
	Value: StringProperty(name='Value', update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)


	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertices')
		self.inputs.new('SvStringsSocket', 'Key').prop_name='Key'
		self.inputs.new('SvStringsSocket', 'Value').prop_name='Value'
		self.outputs.new('SvStringsSocket', 'Vertices')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		vertexList = self.inputs['Vertices'].sv_get(deepcopy=True)
		keyList = self.inputs['Key'].sv_get(deepcopy=True)[0]
		valueList = self.inputs['Value'].sv_get(deepcopy=True)[0]
		inputs = [vertexList, keyList, valueList]
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
			output = processItem(anInput)
			print(output)
			if output:
				outputs.append(output)
		self.outputs['Vertices'].sv_set(outputs)
		end = time.time()
		print("Graph.VerticesAtKeyValue Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphVerticesAtKeyValue)

def unregister():
    bpy.utils.unregister_class(SvGraphVerticesAtKeyValue)
