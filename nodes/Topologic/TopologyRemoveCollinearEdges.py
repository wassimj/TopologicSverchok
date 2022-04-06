import bpy
from bpy.props import StringProperty, FloatProperty
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

def toDegrees(ang):
	import math
	return ang * 180 / math.pi

# From https://gis.stackexchange.com/questions/387237/deleting-collinear-vertices-from-polygon-feature-class-using-arcpy
def are_collinear(v2, wire, tolerance=0.5):
	edges = []
	_ = v2.Edges(wire, edges)
	if len(edges) == 2:
		ang = toDegrees(topologic.EdgeUtility.AngleBetween(edges[0], edges[1]))
		if -tolerance <= ang <= tolerance:
			return True
		else:
			return False
	else:
		raise Exception("Topology.RemoveCollinearEdges - Error: This method only applies to manifold closed wires")

#----------------------------------------------------------------------
def get_redundant_vertices(vertices, wire, angTol):
    """get redundant vertices from a line shape vertices"""
    indexes_of_vertices_to_remove = []
    start_idx, middle_index, end_index = 0, 1, 2
    for i in range(len(vertices)):
        v1, v2, v3 = vertices[start_idx:end_index + 1]
        if are_collinear(v2, wire, angTol):
            indexes_of_vertices_to_remove.append(middle_index)

        start_idx += 1
        middle_index += 1
        end_index += 1
        if end_index == len(vertices):
            break
    if are_collinear(vertices[0], wire, angTol):
        indexes_of_vertices_to_remove.append(0)
    return indexes_of_vertices_to_remove

def processWire(wire, angTol):
	vertices = []
	_ = wire.Vertices(None, vertices)
	redundantIndices = get_redundant_vertices(vertices, wire, angTol)
	# Check if first vertex is also collinear
	if are_collinear(vertices[0], wire, angTol):
		redundantIndices.append(0)
	cleanedVertices = []
	for i in range(len(vertices)):
		if (i in redundantIndices) == False:
			cleanedVertices.append(vertices[i])
	edges = []
	for i in range(len(cleanedVertices)-1):
		edges.append(topologic.Edge.ByStartVertexEndVertex(cleanedVertices[i], cleanedVertices[i+1]))
	edges.append(topologic.Edge.ByStartVertexEndVertex(cleanedVertices[-1], cleanedVertices[0]))
	return topologic.Wire.ByEdges(edges)
	#return topologic.WireUtility.RemoveCollinearEdges(wire, angTol) #This is an angle Tolerance

def processItem(topology, angTol, tolerance):
	returnTopology = topology
	t = topology.Type()
	if (t == 1) or (t == 2) or (t == 128): #Vertex or Edge or Cluster, return the original topology
		return returnTopology
	elif (t == 4): #wire
		returnTopology = processWire(topology, angTol)
		return returnTopology
	elif (t == 8): #Face
		extBoundary = processWire(topology.ExternalBoundary(), angTol)
		internalBoundaries = []
		_ = topology.InternalBoundaries(internalBoundaries)
		cleanIB = []
		for ib in internalBoundaries:
			cleanIB.append(processWire(ib, angTol))
		try:
			returnTopology = topologic.Face.ByExternalInternalBoundaries(extBoundary, cleanIB)
		except:
			returnTopology = topology
		return returnTopology
	faces = []
	_ = topology.Faces(None, faces)
	stl_final_faces = []
	for aFace in faces:
		extBoundary = processWire(aFace.ExternalBoundary(), angTol)
		internalBoundaries = []
		_ = aFace.InternalBoundaries(internalBoundaries)
		cleanIB = []
		for ib in internalBoundaries:
			cleanIB.append(processWire(ib, angTol))
		stl_final_faces.append(topologic.Face.ByExternalInternalBoundaries(extBoundary, cleanIB))
	returnTopology = topology
	if t == 16: # Shell
		try:
			returnTopology = topologic.Shell.ByFaces(stl_final_faces, tolerance)
		except:
			returnTopology = topology
	elif t == 32: # Cell
		try:
			returnTopology = topologic.Cell.ByFaces(stl_final_faces, tolerance)
		except:
			returnTopology = topology
	elif t == 64: #CellComplex
		try:
			returnTopology = topologic.CellComplex.ByFaces(stl_final_faces, tolerance)
		except:
			returnTopology = topology
	return returnTopology

class SvTopologyRemoveCollinearEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Removes any collinear edges from the input Topology    
	"""
	bl_idname = 'SvTopologyRemoveCollinearEdges'
	bl_label = 'Topology.RemoveCollinearEdges'
	AngTol: FloatProperty(name='AngTol', default=0.1, precision=4, update=updateNode)
	Tol: FloatProperty(name='Tol', default=0.0001, min=0, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Angular Tolerance').prop_name='AngTol'
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		angTol = self.inputs['Angular Tolerance'].sv_get(deepcopy=False)[0][0]
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0][0]

		topologyList = flatten(topologyList)
		outputs = []
		for aTopology in topologyList:
			outputs.append(processItem(aTopology, angTol, tol))
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvTopologyRemoveCollinearEdges)

def unregister():
    bpy.utils.unregister_class(SvTopologyRemoveCollinearEdges)
