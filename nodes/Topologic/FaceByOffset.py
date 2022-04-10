import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from . import topologic_lib
import numpy as np
import math

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

def processWire(wire, offset, reverse):
	face = topologic.Face.ByExternalBoundary(wire)
	if reverse:
		offset = -offset
	external_vertices = []
	_ = wire.Vertices(None, external_vertices)
	offset_vertices = []
	for idx in range(len(external_vertices)-1):
		vrtx = [external_vertices[idx].X(), external_vertices[idx].Y(), external_vertices[idx].Z()]
		vrtx1 = [external_vertices[idx+1].X(), external_vertices[idx+1].Y(), external_vertices[idx+1].Z()]
		vrtx2 = [external_vertices[idx-1].X(), external_vertices[idx-1].Y(), external_vertices[idx-1].Z()]
		u = topologic_lib.normalize([(vrtx1[0] - vrtx[0]), (vrtx1[1] - vrtx[1]),(vrtx1[2] - vrtx[2])])
		v = topologic_lib.normalize([(vrtx2[0] - vrtx[0]), (vrtx2[1] - vrtx[1]),(vrtx2[2] - vrtx[2])])
		ev = external_vertices[idx]
		v3 = vrtx + u
		v4 = vrtx + v
		offset_vertex = ([ev.X(), ev.Y(), ev.Z()] + offset * math.sqrt(2 / (1 - np.dot(u, v))) * topologic_lib.normalize(u + v))
		topologic_offset_vertex = topologic.Vertex.ByCoordinates(offset_vertex[0], offset_vertex[1], offset_vertex[2])
		status = (topologic.FaceUtility.IsInside(face, topologic_offset_vertex, 0.001))
		if reverse:
			status = not status
		if status:
			offset = -offset
			offset_vertex = ([ev.X(), ev.Y(), ev.Z()] + offset * math.sqrt(2 / (1 - np.dot(u, v))) * topologic_lib.normalize(u + v))
		offset_vertices.append([ev.X(), ev.Y(), ev.Z()] + offset * math.sqrt(2 / (1 - np.dot(u, v))) * topologic_lib.normalize(u + v))

	idx = len(external_vertices)-1
	v = [external_vertices[idx].X(), external_vertices[idx].Y(), external_vertices[idx].Z()]
	v1 = [external_vertices[0].X(), external_vertices[0].Y(), external_vertices[0].Z()]
	v2 = [external_vertices[idx-1].X(), external_vertices[idx-1].Y(), external_vertices[idx-1].Z()]
	u = topologic_lib.normalize([(v1[0]-v[0]), (v1[1]-v[1]), (v1[2]-v[2])])
	v = topologic_lib.normalize([(v2[0]-v[0]), (v2[1]-v[1]),(v2[2]-v[2])])
	ev = external_vertices[idx]
	offset_vertex = ([ev.X(), ev.Y(), ev.Z()] + offset * math.sqrt(2 / (1 - np.dot(u, v))) * topologic_lib.normalize(u + v))
	topologic_offset_vertex = topologic.Vertex.ByCoordinates(offset_vertex[0], offset_vertex[1], offset_vertex[2])
	status = (topologic.FaceUtility.IsInside(face, topologic_offset_vertex, 0.001))
	if reverse:
		status = not status
	if status:
		offset = -offset
		offset_vertex = ([ev.X(), ev.Y(), ev.Z()] + offset * math.sqrt(2 / (1 - np.dot(u, v))) * topologic_lib.normalize(u + v))
	offset_vertices.append([ev.X(), ev.Y(), ev.Z()] + offset * math.sqrt(2 / (1 - np.dot(u, v))) * topologic_lib.normalize(u + v))
	edges = []
	for iv, v in enumerate(offset_vertices[:-1]):
		e = topologic.Edge.ByStartVertexEndVertex(topologic.Vertex.ByCoordinates(offset_vertices[iv][0], offset_vertices[iv][1], offset_vertices[iv][2]), topologic.Vertex.ByCoordinates(offset_vertices[iv+1][0], offset_vertices[iv+1][1], offset_vertices[iv+1][2]))
		edges.append(e)
	iv = len(offset_vertices)-1
	e = topologic.Edge.ByStartVertexEndVertex(topologic.Vertex.ByCoordinates(offset_vertices[iv][0], offset_vertices[iv][1], offset_vertices[iv][2]), topologic.Vertex.ByCoordinates(offset_vertices[0][0], offset_vertices[0][1], offset_vertices[0][2]))
	edges.append(e)
	return topologic.Wire.ByEdges(edges)

def processItem(item):
	face, offset, reverse, tolerance = item
	external_boundary = face.ExternalBoundary()
	internal_boundaries = []
	_ = face.InternalBoundaries(internal_boundaries)
	offset_external_boundary = processWire(external_boundary, offset, reverse)
	offset_external_face = topologic.Face.ByExternalBoundary(offset_external_boundary)
	if topologic.FaceUtility.Area(offset_external_face) < tolerance:
		raise Exception("ERROR: (Topologic>Face.ByOffset) external boundary area is less than tolerance.")
	offset_internal_boundaries = []
	reverse = not reverse
	area_sum = 0
	for internal_boundary in internal_boundaries:
		internal_wire = processWire(internal_boundary, offset, reverse)
		internal_face = topologic.Face.ByExternalBoundary(internal_wire)
		# Check if internal boundary has a trivial area
		if topologic.FaceUtility.Area(internal_face) < tolerance:
			raise Exception("ERROR: (Topologic>Face.ByOffset) internal boundary area is less than tolerance.")
		# Check if area of internal boundary is larger than area of external boundary
		if topologic.FaceUtility.Area(internal_face) > topologic.FaceUtility.Area(offset_external_face):
			raise Exception("ERROR: (Topologic>Face.ByOffset) internal boundary area is larger than the area of the external boundary.")
		dif_wire = internal_wire.Difference(offset_external_boundary)
		internal_vertices = []
		_ = internal_wire.Vertices(None, internal_vertices)
		dif_vertices = []
		_ = dif_wire.Vertices(None, dif_vertices)
		# Check if internal boundary intersect the outer boundary
		if len(internal_vertices) != len(dif_vertices):
			raise Exception("ERROR: (Topologic>Face.ByOffset) internal boundaries intersect outer boundary.")
		offset_internal_boundaries.append(internal_wire)
		area_sum = area_sum + topologic.FaceUtility.Area(internal_face)
	if area_sum > topologic.FaceUtility.Area(offset_external_face):
		raise Exception("ERROR: (Topologic>Face.ByOffset) total area of internal boundaries is larger than the area of the external boundary.")
	# NOT IMPLEMENTED: Check if internal boundaries intersect each other!
	returnFace = topologic.Face.ByExternalInternalBoundaries(offset_external_boundary, offset_internal_boundaries)
	if returnFace.Type() != 8:
		raise Exception("ERROR: (Topologic>Face.ByOffset) invalid resulting face.")
	if topologic.FaceUtility.Area(returnFace) < tolerance:
		raise Exception("ERROR: (Topologic>Face.ByOffset) area of resulting face is smaller than the tolerance.")
	return returnFace

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvFaceByOffset(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face by offsetting the input Face    
	"""
	bl_idname = 'SvFaceByOffset'
	bl_label = 'Face.ByOffset'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Offset: FloatProperty(name="Offset", default=0, min=0, precision=4, update=updateNode)
	Reverse: BoolProperty(name="Reverse", default=False, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'Offset').prop_name = 'Offset'
		self.inputs.new('SvStringsSocket', 'Reverse').prop_name = 'Reverse'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		faceList = flatten(faceList)
		offsetList = self.inputs['Offset'].sv_get(deepcopy=False)
		offsetList = flatten(offsetList)
		reverseList = self.inputs['Reverse'].sv_get(deepcopy=False)
		reverseList = flatten(reverseList)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		toleranceList = flatten(toleranceList)
		inputs = [faceList, offsetList, reverseList, toleranceList]
		if ((self.Replication) == "Default"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
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
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceByOffset)

def unregister():
	bpy.utils.unregister_class(SvFaceByOffset)
