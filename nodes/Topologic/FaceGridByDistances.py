import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
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

def processItem(item):
	face = item[0]
	uRange = item[1]
	vRange = item[2]
	uOrigin = item[3]
	vOrigin = item[4]
	clip = item[5]
	if isinstance(clip, list):
		clip = clip[0]
	uvWireEdges = []
	uCluster = None
	vCluster = None
	uvWire = None
	v1 = topologic.FaceUtility.VertexAtParameters(face, 0, 0)
	v2 = topologic.FaceUtility.VertexAtParameters(face, 1, 0)
	uVector = [v2.X()-v1.X(), v2.Y()-v1.Y(),v2.Z()-v1.Z()]
	v1 = topologic.FaceUtility.VertexAtParameters(face, 0, 0)
	v2 = topologic.FaceUtility.VertexAtParameters(face, 0, 1)
	vVector = [v2.X()-v1.X(), v2.Y()-v1.Y(),v2.Z()-v1.Z()]
	if len(uRange) > 0:
		uRange.sort()
		uRangeEdges = []
		uuVector = unitizeVector(uVector)
		for u in uRange:
			tempVec = multiplyVector(uuVector, u, 0.0001)
			v1 = topologic.Vertex.ByCoordinates(uOrigin.X()+tempVec[0], uOrigin.Y()+tempVec[1], uOrigin.Z()+tempVec[2])
			v2 = topologic.Vertex.ByCoordinates(v1.X()+vVector[0], v1.Y()+vVector[1], v1.Z()+vVector[2])
			e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
			uRangeEdges.append(e)
			uvWireEdges.append(e)
		if len(uRangeEdges) > 0:
			uCluster = topologic.Cluster.ByTopologies(uRangeEdges)
			if clip:
				uCluster = uCluster.Intersect(face, False)
	if len(vRange) > 0:
		vRange.sort()
		vRangeEdges = []
		uvVector = unitizeVector(vVector)
		for v in vRange:
			tempVec = multiplyVector(uvVector, v, 0.0001)
			v1 = topologic.Vertex.ByCoordinates(vOrigin.X()+tempVec[0], vOrigin.Y()+tempVec[1], vOrigin.Z()+tempVec[2])
			v2 = topologic.Vertex.ByCoordinates(v1.X()+uVector[0], v1.Y()+uVector[1], v1.Z()+uVector[2])
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

class SvFaceGridByDistances(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a grid of edges based on the input face and input distances    
	"""
	bl_idname = 'SvFaceGridByDistances'
	bl_label = 'Face.GridByDistances'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Clip: BoolProperty(name="Clip To Face", default=True, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'uRange')
		self.inputs.new('SvStringsSocket', 'vRange')
		self.inputs.new('SvStringsSocket', 'uOrigin')
		self.inputs.new('SvStringsSocket', 'vOrigin')
		self.inputs.new('SvStringsSocket', 'Clip').prop_name = 'Clip'
		self.outputs.new('SvStringsSocket', 'u')
		self.outputs.new('SvStringsSocket', 'v')
		self.outputs.new('SvStringsSocket', 'uv')

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
		if not (self.inputs['uOrigin'].is_linked):
			uOriginList = []
			for aFace in faceList:
				uOriginList.append(topologic.FaceUtility.VertexAtParameters(aFace, 0, 0))
		else:
			uOriginList = self.inputs['uOrigin'].sv_get(deepcopy=True)
			uOriginList = flatten(uOriginList)
		if not (self.inputs['vOrigin'].is_linked):
			vOriginList = []
			for aFace in faceList:
				vOriginList.append(topologic.FaceUtility.VertexAtParameters(aFace, 0, 0))
		else:
			vOriginList = self.inputs['vOrigin'].sv_get(deepcopy=True)
			vOriginList = flatten(vOriginList)
		if self.inputs['uRange'].is_linked:
			uRangeList = self.inputs['uRange'].sv_get(deepcopy=False)
		else:
			uRangeList = []
		if self.inputs['vRange'].is_linked:
			vRangeList = self.inputs['vRange'].sv_get(deepcopy=False)
		else:
			vRangeList = []
		inputs = [faceList, uRangeList, vRangeList, uOriginList, vOriginList, clipList]
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
	bpy.utils.register_class(SvFaceGridByDistances)

def unregister():
	bpy.utils.unregister_class(SvFaceGridByDistances)
