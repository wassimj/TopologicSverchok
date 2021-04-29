import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy
import numpy
from numpy.linalg import norm
from numpy import dot
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
			print("Removing a Face")
			faces.remove(aFace)
			return faces
	return faces

def shellToFace(shell):
	externalEdges = cppyy.gbl.std.list[topologic.Topology.Ptr]()
	shellEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	_ = shell.Edges(shellEdges)
	for shellEdge in shellEdges:
		stl_edgeFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = shellEdge.Faces(stl_edgeFaces)
		edgeFaces = list(stl_edgeFaces)
		if len(edgeFaces) < 2:
			externalEdges.push_back(shellEdge)
	cluster = topologic.Cluster.ByTopologies(externalEdges)
	cluster = cluster.SelfMerge()
	# This cluster could be made of more than 1 wire
	stl_wires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	_ = cluster.Wires(stl_wires)
	wires = []
	areas = []
	for aWire in stl_wires:
		aWire = topologic.WireUtility.RemoveCollinearEdges(aWire, 0.1)
		ib = cppyy.gbl.std.list[topologic.Wire.Ptr]()
		#wireVertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		#_ = aWire.Vertices(wireVertices)
		#poly = []
		#for aVertex in wireVertices:
		#	poly.append((aVertex.X(), aVertex.Y(), aVertex.Z()))
		#areas.append(poly_area(poly))
		face = topologic.Face.ByExternalInternalBoundaries(aWire, ib)
		#faces.append(face)
		wires.append(aWire)
		areas.append(topologic.FaceUtility.Area(face))
	wires = [x for _, x in sorted(zip(areas, wires))] #Sort wires according to their areas
	ib = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	for internalWire in wires[0:len(wires)-1]:
		ib.push_back(internalWire)
	finalFace = topologic.Face.ByExternalInternalBoundaries(wires[-1], ib)
	return finalFace

def match(faceA, faceB, angTol):
	if topologic.Topology.IsSame(faceA, faceB):
		print("FAILED IsSame Test")
		return False
	edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	faceA.SharedEdges(faceB, edges)
	edges = list(edges)
	if len(edges) < 1:
		print("FAILED SharedEdges Test")
		return False
	# Compute the normal of each face
	n1 = topologic.FaceUtility.NormalAtParameters(faceA,0.5, 0.5)
	v1 = [n1.X(), n1.Y(), n1.Z()]
	n2 = topologic.FaceUtility.NormalAtParameters(faceB,0.5, 0.5)
	v2 = [n2.X(), n2.Y(), n2.Z()]
	# Compute the angle between the two Faces
	ang = angle(v1, v2)
	if (ang > angTol):
		print("FAILED Angle Test with: "+ str(ang))
		return False
	print("SUCCESS! Found a Matched Face")
	return True

def findCoplanarFaces(faceA, faces, angTol, matchedFaces):
	for faceB in faces:
		if not faceB in matchedFaces:
			if match(faceA, faceB, angTol):
				matchedFaces.append(faceB)
				matchedFaces = findCoplanarFaces(faceB, faces, angTol, matchedFaces)
	return matchedFaces

def processItemNew(cell, angTol):
	# Get the faces of the Cell
	faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	_ = cell.Faces(faces)
	faces = list(faces)
	finalFaces = faces.copy()
	for faceA in faces:
		matchedFaces = [faceA]
		matchedFaces = findCoplanarFaces(faceA, faces, angTol, matchedFaces)
		print(matchedFaces)
		if (len(matchedFaces) > 1):
			stl_matched_faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
			for matchedFace in matchedFaces:
				stl_matched_faces.push_back(matchedFace)
			shell = topologic.Shell.ByFaces(stl_matched_faces)
			print(shell)
			newFace = shellToFace(shell)
			finalFaces.append(newFace)
			for matchedFace in matchedFaces:
				finalFaces = removeFace(matchedFace, finalFaces)
	stl_final_faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	for aFace in finalFaces:
		stl_final_faces.push_back(aFace)
	return (topologic.Cell.ByFaces(stl_final_faces))

def processItem(cell, angTol):
	# Get the edges of the Cell
	edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	_ = cell.Edges(edges)
	# Get the faces of the Cell
	stl_faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	_ = cell.Faces(stl_faces)
	cellFaces = list(stl_faces)
	debug = []
	# Loop through the Edges.
	for anEdge in edges:
		# Get the faces of the edge. Each edge has two faces that it connects
		stl_edge_faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = anEdge.Faces(stl_edge_faces)
		faces = list(stl_edge_faces)
		# Compute the normal of each face
		n1 = topologic.FaceUtility.NormalAtParameters(faces[0],0.5, 0.5)
		v1 = [n1.X(), n1.Y(), n1.Z()]
		n2 = topologic.FaceUtility.NormalAtParameters(faces[1],0.5, 0.5)
		v2 = [n2.X(), n2.Y(), n2.Z()]
		# Compute the angle between the two Faces
		ang = angle(v1, v2)
		print(ang)
		# If the angle is less than the tolerance, the two faces need to be replaced

		if (ang < angTol) or (abs(ang - 180) < angTol):
			# Create a Shell out of the two faces
			shell = topologic.Shell.ByFaces(stl_edge_faces)
			print("get the external boundary of the shell")
			# Get the external boundary wire of the shell, cleaned up.
			newFace = shellToFace(shell)
			debug.append(newFace)
			cellFaces.append(newFace)
			# remove the two faces from the list of
			cellFaces = removeFace(faces[0], cellFaces)
			cellFaces = removeFace(faces[1], cellFaces)

	stl_final_faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	for aFace in cellFaces:
		stl_final_faces.push_back(aFace)
	return (topologic.Cell.ByFaces(stl_final_faces))

class SvCellRemoveCoplanarFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Removes any coplanar faces from the input Cell    
	"""
	bl_idname = 'SvCellRemoveCoplanarFaces'
	bl_label = 'Cell.RemoveCoplanarFaces'
	AngTol: FloatProperty(name='AngTol', default=0.1, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cell')
		self.inputs.new('SvStringsSocket', 'Angular Tolerance').prop_name='AngTol'
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		cells = self.inputs['Cell'].sv_get(deepcopy=False)
		angTol = self.inputs['Angular Tolerance'].sv_get(deepcopy=False)[0][0]

		cells = flatten(cells)
		output = []
		for aCell in cells:
			output.append(processItemNew(aCell, angTol))
		output = flatten(output)
		self.outputs['Cell'].sv_set(output)
		end = time.time()
		print("Cell.RemoveCoplanarFaces Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvCellRemoveCoplanarFaces)

def unregister():
    bpy.utils.unregister_class(SvCellRemoveCoplanarFaces)
