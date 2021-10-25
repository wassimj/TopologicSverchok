import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time
import math
import itertools

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

# Python program to find if two lists are cyclically equivalent
# for example [1,2,3,4] is cyclically equivalent to [3,4,1,2]
# Adapted from https://stackoverflow.com/questions/31000591/check-if-a-list-is-a-rotation-of-another-list-that-works-with-duplicates

def isCyclicallyEquivalent(u, v, lengthTolerance, angleTolerance):
	n, i, j = len(u), 0, 0
	if n != len(v):
		return False
	while i < n and j < n:
		if (i % 2) == 0:
			tol = lengthTolerance
		else:
			tol = angleTolerance
		k = 1
		while k <= n and math.fabs(u[(i + k) % n]- v[(j + k) % n]) <= tol:
			k += 1
		if k > n:
			return True
		if math.fabs(u[(i + k) % n]- v[(j + k) % n]) > tol:
			i += k
		else:
			j += k
	return False

def angleBetweenEdges(e1, e2, tolerance):
	a = e1.EndVertex().X() - e1.StartVertex().X()
	b = e1.EndVertex().Y() - e1.StartVertex().Y()
	c = e1.EndVertex().Z() - e1.StartVertex().Z()
	d = topologic.VertexUtility.Distance(e1.EndVertex(), e2.StartVertex())
	if d <= tolerance:
		d = e2.StartVertex().X() - e2.EndVertex().X()
		e = e2.StartVertex().Y() - e2.EndVertex().Y()
		f = e2.StartVertex().Z() - e2.EndVertex().Z()
	else:
		d = e2.EndVertex().X() - e2.StartVertex().X()
		e = e2.EndVertex().Y() - e2.StartVertex().Y()
		f = e2.EndVertex().Z() - e2.StartVertex().Z()
	dotProduct = a*d + b*e + c*f
	modOfVector1 = math.sqrt( a*a + b*b + c*c)*math.sqrt(d*d + e*e + f*f) 
	angle = dotProduct/modOfVector1
	angleInDegrees = math.degrees(math.acos(angle))
	return angleInDegrees

def getInteriorAngles(edges, tolerance):
	angles = []
	for i in range(len(edges)-1):
		e1 = edges[i]
		e2 = edges[i+1]
		angles.append(angleBetweenEdges(e1, e2, tolerance))
	return angles

def getRep(edges, tolerance):
	angles = getInteriorAngles(edges, tolerance)
	lengths = []
	for anEdge in edges:
		lengths.append(topologic.EdgeUtility.Length(anEdge))
	minLength = min(lengths)
	normalisedLengths = []
	for aLength in lengths:
		normalisedLengths.append(aLength/minLength)
	return [x for x in itertools.chain(*itertools.zip_longest(normalisedLengths, angles)) if x is not None]

def processItem(item):
	wireA = item[0]
	wireB = item[1]
	if (wireA.IsClosed() == False):
		raise Exception("Error: Wire.IsSimilar - Wire A is not closed.")
	if (wireB.IsClosed() == False):
		raise Exception("Error: Wire.IsSimilar - Wire B is not closed.")
	edgesA = []
	_ = wireA.Edges(edgesA)
	edgesB = []
	_ = wireB.Edges(edgesB)
	if len(edgesA) != len(edgesB):
		return False
	lengthTolerance = item[2]
	angleTolerance = item[3]
	repA = getRep(list(edgesA), lengthTolerance)
	repB = getRep(list(edgesB), lengthTolerance)
	if isCyclicallyEquivalent(repA, repB, lengthTolerance, angleTolerance):
		return True
	if isCyclicallyEquivalent(repA, repB[::-1], lengthTolerance, angleTolerance):
		return True
	return False

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvWireIsSimilar(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the input Wires are similar. Outputs False otherwise   
	"""
	bl_idname = 'SvWireIsSimilar'
	bl_label = 'Wire.IsSimilar'
	Bool: BoolProperty(name="Bool", default=False, update=updateNode)
	LengthTolerance: FloatProperty(name="Length Tolerance",  default=0.001, precision=4, update=updateNode)
	AngleTolerance: FloatProperty(name="Angle Tolerance",  default=0.1, precision=2, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire A')
		self.inputs.new('SvStringsSocket', 'Wire B')
		self.inputs.new('SvStringsSocket', 'Length Tolerance').prop_name = 'LengthTolerance'
		self.inputs.new('SvStringsSocket', 'Angle Tolerance').prop_name = 'AngleTolerance'
		self.outputs.new('SvStringsSocket', 'Is Similar').prop_name = 'Bool'

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		wireAList = self.inputs['Wire A'].sv_get(deepcopy=True)
		wireBList = self.inputs['Wire B'].sv_get(deepcopy=True)
		lengthToleranceList = self.inputs['Length Tolerance'].sv_get(deepcopy=True)
		angleToleranceList = self.inputs['Angle Tolerance'].sv_get(deepcopy=True)
		wireAList = flatten(wireAList)
		wireBList = flatten(wireBList)
		lengthToleranceList = flatten(lengthToleranceList)
		angleToleranceList = flatten(angleToleranceList)

		inputs = [wireAList, wireBList, lengthToleranceList, angleToleranceList]
		if ((self.Replication) == "Default"):
			inputs = iterate(inputs)
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
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Is Similar'].sv_set(outputs)
		end = time.time()
		print("Wire.IsSimilar Operation consumed "+str(round(end - start,2))+" seconds")

def register():
	bpy.utils.register_class(SvWireIsSimilar)

def unregister():
	bpy.utils.unregister_class(SvWireIsSimilar)
