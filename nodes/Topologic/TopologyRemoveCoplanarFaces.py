import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

try:
	import numpy
	from numpy.linalg import norm
	from numpy import dot
except:
	raise Exception("Error: Could not import numpy.")
import math
import time

#from https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates

#unit normal vector of plane defined by points a, b, and c
def unit_normal(a, b, c):
    x = numpy.linalg.det([[1,a[1],a[2]],
         [1,b[1],b[2]],
         [1,c[1],c[2]]])
    y = numpy.linalg.det([[a[0],1,a[2]],
         [b[0],1,b[2]],
         [c[0],1,c[2]]])
    z = numpy.linalg.det([[a[0],a[1],1],
         [b[0],b[1],1],
         [c[0],c[1],1]])
    magnitude = (x**2 + y**2 + z**2)**.5
    return (x/magnitude, y/magnitude, z/magnitude)

#area of polygon poly
def poly_area(poly):
    if len(poly) < 3: # not a plane - no area
        return 0
    total = [0, 0, 0]
    N = len(poly)
    for i in range(N):
        vi1 = poly[i]
        vi2 = poly[(i+1) % N]
        prod = numpy.cross(vi1, vi2)
        total[0] += prod[0]
        total[1] += prod[1]
        total[2] += prod[2]
    result = numpy.dot(total, unit_normal(poly[0], poly[1], poly[2]))
    return abs(result/2)

# From https://stackoverflow.com/questions/9875964/how-can-i-convert-radians-to-degrees-with-python
def angle(a, b):
	arccosInput = dot(a,b)/norm(a)/norm(b)
	arccosInput = 1.0 if arccosInput > 1.0 else arccosInput
	arccosInput = -1.0 if arccosInput < -1.0 else arccosInput
	return math.degrees(math.acos(arccosInput))

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def removeFace(face, faces):
	for aFace in faces:
		if topologic.Topology.IsSame(aFace, face):
			faces.remove(aFace)
			return faces
	return faces

def shellToFace(shell):
	externalEdges = []
	shellEdges = []
	_ = shell.Edges(shellEdges)
	for shellEdge in shellEdges:
		edgeFaces = []
		_ = shellEdge.Faces(edgeFaces)
		if len(edgeFaces) < 2:
			externalEdges.append(shellEdge)
	cluster = topologic.Cluster.ByTopologies(externalEdges)
	cluster = cluster.SelfMerge()
	# This cluster could be made of more than 1 wire
	stl_wires = []
	_ = cluster.Wires(stl_wires)
	wires = []
	areas = []
	for aWire in stl_wires:
		print("BEFORE")
		print(aWire)
		aWire = topologic.WireUtility.RemoveCollinearEdges(aWire, 0.1)
		print("AFTER")
		print(aWire)
		if(aWire):
			face = topologic.Face.ByExternalBoundary(aWire)
			wires.append(aWire)
			areas.append(topologic.FaceUtility.Area(face))
	wires = [x for _, x in sorted(zip(areas, wires))] #Sort wires according to their areas
	print(wires)
	ib = []
	for internalWire in wires[0:len(wires)-1]:
		ib.append(internalWire)
	finalFace = topologic.Face.ByExternalInternalBoundaries(wires[-1], ib)
	return finalFace

def match(faceA, faceB, angTol):
	if topologic.Topology.IsSame(faceA, faceB):
		return False
	edges = []
	faceA.SharedEdges(faceB, edges)
	if len(edges) < 1:
		return False
	# Compute the normal of each face
	n1 = topologic.FaceUtility.NormalAtParameters(faceA,0.5, 0.5)
	v1 = [n1[0], n1[1], n1[2]]
	n2 = topologic.FaceUtility.NormalAtParameters(faceB,0.5, 0.5)
	v2 = [n2[0], n2[1], n2[2]]
	# Compute the angle between the two Faces
	ang = angle(v1, v2)
	if (ang > angTol):
		return False
	return True

def findCoplanarFaces(faceA, faces, angTol, matchedFaces):
	for faceB in faces:
		if not faceB in matchedFaces:
			if match(faceA, faceB, angTol):
				matchedFaces.append(faceB)
				matchedFaces = findCoplanarFaces(faceB, faces, angTol, matchedFaces)
	return matchedFaces

def processItem(topology, angTol, tolerance):
	t = topology.Type()
	if (t == 1) or (t == 2) or (t == 4) or (t == 8) or (t == 128):
		return topology
	# Get the faces of the Topology
	faces = []
	_ = topology.Faces(faces)
	finalFaces = faces.copy()
	for faceA in faces:
		matchedFaces = [faceA]
		matchedFaces = findCoplanarFaces(faceA, faces, angTol, matchedFaces)
		if (len(matchedFaces) > 1):
			stl_matched_faces = []
			for matchedFace in matchedFaces:
				stl_matched_faces.append(matchedFace)
			shell = topologic.Shell.ByFaces(stl_matched_faces)
			newFace = shellToFace(shell)
			finalFaces.append(newFace)
			for matchedFace in matchedFaces:
				finalFaces = removeFace(matchedFace, finalFaces)
	returnTopology = topology
	if t == 16: # Shell
		try:
			returnTopology = topologic.Shell.ByFaces(finalFaces, tolerance)
		except:
			returnTopology = topology
	elif t == 32: # Cell
		try:
			returnTopology = topologic.Cell.ByFaces(finalFaces, tolerance)
		except:
			returnTopology = topology
	elif t == 64: #CellComplex
		try:
			returnTopology = topologic.CellComplex.ByFaces(finalFaces, tolerance)
		except:
			returnTopology = topology
	return returnTopology

class SvTopologyRemoveCoplanarFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Removes any coplanar faces from the input Topology    
	"""
	bl_idname = 'SvTopologyRemoveCoplanarFaces'
	bl_label = 'Topology.RemoveCoplanarFaces'
	AngTol: FloatProperty(name='AngTol', default=0.1, min=0, precision=4, update=updateNode)
	Tol: FloatProperty(name='Tol', default=0.0001, min=0, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Angular Tolerance').prop_name='AngTol'
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		angTol = self.inputs['Angular Tolerance'].sv_get(deepcopy=False)[0][0]
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0][0]
		topologyList = flatten(topologyList)
		outputs = []
		for aTopology in topologyList:
			outputs.append(processItem(aTopology, angTol, tol))
		outputs = flatten(outputs)
		self.outputs['Topology'].sv_set(outputs)
		end = time.time()
		print("Topology.RemoveCoplanarFaces Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyRemoveCoplanarFaces)

def unregister():
    bpy.utils.unregister_class(SvTopologyRemoveCoplanarFaces)
