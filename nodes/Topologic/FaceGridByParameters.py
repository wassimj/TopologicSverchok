import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
#import Replication
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

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

def selfMerge(item):
	resultingTopologies = []
	topCC = []
	_ = item.CellComplexes(None, topCC)
	topCells = []
	_ = item.Cells(None, topCells)
	topShells = []
	_ = item.Shells(None, topShells)
	topFaces = []
	_ = item.Faces(None, topFaces)
	topWires = []
	_ = item.Wires(None, topWires)
	topEdges = []
	_ = item.Edges(None, topEdges)
	topVertices = []
	_ = item.Vertices(None, topVertices)
	if len(topCC) == 1:
		cc = topCC[0]
		ccVertices = []
		_ = cc.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(cc)
	if len(topCC) == 0 and len(topCells) == 1:
		cell = topCells[0]
		ccVertices = []
		_ = cell.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(cell)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 1:
		shell = topShells[0]
		ccVertices = []
		_ = shell.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(shell)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 1:
		face = topFaces[0]
		ccVertices = []
		_ = face.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(face)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 1:
		wire = topWires[0]
		ccVertices = []
		_ = wire.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(wire)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 0 and len(topEdges) == 1:
		edge = topEdges[0]
		ccVertices = []
		_ = wire.Vertices(None, ccVertices)
		if len(topVertices) == len(ccVertices):
			resultingTopologies.append(edge)
	if len(topCC) == 0 and len(topCells) == 0 and len(topShells) == 0 and len(topFaces) == 0 and len(topWires) == 0 and len(topEdges) == 0 and len(topVertices) == 1:
		vertex = topVertices[0]
		resultingTopologies.append(vertex)
	if len(resultingTopologies) == 1:
		return resultingTopologies[0]
	return item.SelfMerge()

def processItem(item):
	face = item[0]
	uRange = item[1]
	vRange = item[2]
	clip = item[3]
	if isinstance(clip, list):
		clip = clip[0]
	uvWireEdges = []
	uCluster = None
	vCluster = None
	uvWire = None
	if len(uRange) > 0:
		if (min(uRange) < 0) or (max(uRange) > 1):
			raise Exception("Face.GridByParameters - Error: uRange input values are outside acceptable range (0,1)")
		uRange.sort()
		uRangeEdges = []
		for u in uRange:
			v1 = topologic.FaceUtility.VertexAtParameters(face, u, 0)
			v2 = topologic.FaceUtility.VertexAtParameters(face, u, 1)
			e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
			uRangeEdges.append(e)
			uvWireEdges.append(e)
		if len(uRangeEdges) > 0:
			uCluster = topologic.Cluster.ByTopologies(uRangeEdges)
			if clip:
				uCluster = uCluster.Intersect(face, False)
	if len(vRange) > 0:
		if (min(vRange) < 0) or (max(vRange) > 1):
			raise Exception("Face.GridByParameters - Error: vRange input values are outside acceptable range (0,1)")
		vRange.sort()
		vRangeEdges = []
		for v in vRange:
			v1 = topologic.FaceUtility.VertexAtParameters(face, 0, v)
			v2 = topologic.FaceUtility.VertexAtParameters(face, 1, v)
			e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
			vRangeEdges.append(e)
			uvWireEdges.append(e)
		if len(vRangeEdges) > 0:
			vCluster = topologic.Cluster.ByTopologies(vRangeEdges)
			if clip:
				vCluster = vCluster.Intersect(face, False)
	if len(uvWireEdges) > 0 and uCluster and vCluster:
		uvWire = uCluster.Merge(vCluster)
	return [uCluster, vCluster, uvWire]

class SvFaceGridByParameters(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a grid of edges based on the input face and input parameters    
	"""
	bl_idname = 'SvFaceGridByParameters'
	bl_label = 'Face.GridByParameters'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Clip: BoolProperty(name="Clip To Face", default=True, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'uRange')
		self.inputs.new('SvStringsSocket', 'vRange')
		self.inputs.new('SvStringsSocket', 'Clip').prop_name = 'Clip'
		self.outputs.new('SvStringsSocket', 'u')
		self.outputs.new('SvStringsSocket', 'v')
		self.outputs.new('SvStringsSocket', 'uv')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(outputSocket.is_linked for outputSocket in self.outputs):
			return
		if not (self.inputs['Face'].is_linked):
			for outputSocket in self.outputs:
				outputSocket.sv_set([])
			return
		if (not (self.inputs['uRange'].is_linked)) and (not (self.inputs['vRange'].is_linked)):
			for outputSocket in self.outputs:
				outputSocket.sv_set([])
			return
		faceList = self.inputs['Face'].sv_get(deepcopy=True)
		faceList = flatten(faceList)
		clipList = self.inputs['Clip'].sv_get(deepcopy=True)
		clipList = flatten(clipList)
		if not (self.inputs['uRange'].is_linked):
			uRangeList = [[]]
		else:
			uRangeList = self.inputs['uRange'].sv_get(deepcopy=False)
		if not (self.inputs['vRange'].is_linked):
			vRangeList = [[]]
		else:
			vRangeList = self.inputs['vRange'].sv_get(deepcopy=False)
		inputs = [faceList, uRangeList, vRangeList, clipList]
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
		u = []
		v = []
		uv = []
		for anInput in inputs:
			output = processItem(anInput)
			u.append(output[0])
			v.append(output[1])
			uv.append(output[2])
		self.outputs['u'].sv_set(u)
		self.outputs['v'].sv_set(v)
		self.outputs['uv'].sv_set(uv)

def register():
	bpy.utils.register_class(SvFaceGridByParameters)

def unregister():
	bpy.utils.unregister_class(SvFaceGridByParameters)
