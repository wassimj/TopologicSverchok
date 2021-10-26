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

def processWire(wire, angTol):
	return topologic.WireUtility.RemoveCollinearEdges(wire, angTol) #This is an angle Tolerance

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
			cleanIB.push_back(processWire(ib, angTol))
		try:
			returnTopology = topologic.Face.ByExternalInternalBoundaries(extBoundary, cleanIB)
		except:
			returnTopology = topology
		return returnTopology
	faces = []
	_ = topology.Faces(faces)
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
