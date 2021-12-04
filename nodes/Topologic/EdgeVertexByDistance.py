import bpy
from bpy.props import FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

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

def unitizeVector(vector):
	mag = 0
	for value in vector:
		mag += value ** 2
	mag = mag ** 0.5
	unitVector = []
	for i in range(len(vector)):
		unitVector.append(vector[i] / mag)
	return unitVector

def multiplyVector(vector, mag, tol):
	oldMag = 0
	for value in vector:
		oldMag += value ** 2
	oldMag = oldMag ** 0.5
	if oldMag < tol:
		return [0,0,0]
	newVector = []
	for i in range(len(vector)):
		newVector.append(vector[i] * mag / oldMag)
	return newVector

def processItem(item, tol):
	edge = item[0]
	vertex = item[1]
	distance = item[2]
	rv = None
	sv = edge.StartVertex()
	ev = edge.EndVertex()
	vx = ev.X() - sv.X()
	vy = ev.Y() - sv.Y()
	vz = ev.Z() - sv.Z()
	vector = unitizeVector([vx, vy, vz])
	vector = multiplyVector(vector, distance, tol)
	if vertex == None:
		vertex = sv
	rv = topologic.Vertex.ByCoordinates(vertex.X()+vector[0], vertex.Y()+vector[1], vertex.Z()+vector[2])
	return rv

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvEdgeVertexByDistance(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Vertex at the distance from the start Vertex of the input Edge or an optional Vertex
	"""
	bl_idname = 'SvEdgeVertexByDistance'
	bl_label = 'Edge.VertexByDistance'
	Parameter: FloatProperty(name="Distance", default=1.0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.inputs.new('SvStringsSocket', 'Distance').prop_name='Parameter'
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Vertex')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not self.inputs['Edge'].is_linked:
			return
		edgeList = self.inputs['Edge'].sv_get(deepcopy=True)
		edgeList = flatten(edgeList)
		if not (self.inputs['Origin'].is_linked):
			vertexList = []
			for anEdge in edgeList:
				vertexList.append(anEdge.StartVertex())
		else:
			vertexList = self.inputs['Origin'].sv_get(deepcopy=True)
			vertexList = flatten(vertexList)
		distanceList = self.inputs['Distance'].sv_get(deepcopy=True)
		distanceList = flatten(distanceList)
		tol = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)[0][0]
		inputs = [edgeList, vertexList, distanceList]
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
			outputs.append(processItem(anInput, tol))
		self.outputs['Vertex'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEdgeVertexByDistance)

def unregister():
	bpy.utils.unregister_class(SvEdgeVertexByDistance)
