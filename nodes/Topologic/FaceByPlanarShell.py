import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import ShellExternalBoundary, WireByVertices, VertexProject, WireRemoveCollinearEdges

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def list_level_iter(lst, level, _current_level: int= 1):
	"""
	Iterate over all lists with given nesting
	With level 1 it will return the given list
	With level 2 it will iterate over all nested lists in the main one
	If a level does not have lists on that level it will return empty list
	_current_level - for internal use only
	"""
	if _current_level < level:
		try:
			for nested_lst in lst:
				if not isinstance(nested_lst, list):
					raise TypeError
				yield from list_level_iter(nested_lst, level, _current_level + 1)
		except TypeError:
			yield []
	else:
		yield lst

def planarize(wire):
	verts = []
	_ = wire.Vertices(None, verts)
	w = WireByVertices.processItem([[verts[0], verts[1], verts[2]], True])
	f = topologic.Face.ByExternalBoundary(w)
	proj_verts = []
	for v in verts:
		proj_verts.append(VertexProject.processItem([v, f]))
	new_w = WireByVertices.processItem([proj_verts, True])
	return new_w

def planarizeList(wireList):
	returnList = []
	for aWire in wireList:
		returnList.append(planarize(aWire))
	return returnList

def processItem(item):
	shell, angTol = item
	ext_boundary = ShellExternalBoundary.processItem(shell)
	if isinstance(ext_boundary, topologic.Wire):
		try:
			return topologic.Face.ByExternalBoundary(WireRemoveCollinearEdges.processItem(ext_boundary, angTol))
		except:
			try:
				return topologic.Face.ByExternalBoundary(planarize(WireRemoveCollinearEdges.processItem(ext_boundary, angTol)))
			except:
				print("FaceByPlanarShell - Error: The input Wire is not planar and could not be fixed. Returning the planarized Wire.")
				return planarize(ext_boundary)
	elif isinstance(ext_boundary, topologic.Cluster):
		wires = []
		_ = ext_boundary.Wires(None, wires)
		faces = []
		areas = []
		for aWire in wires:
			try:
				aFace = topologic.Face.ByExternalBoundary(WireRemoveCollinearEdges.processItem(aWire, angTol))
			except:
				aFace = topologic.Face.ByExternalBoundary(planarize(WireRemoveCollinearEdges.processItem(aWire, angTol)))
			anArea = topologic.FaceUtility.Area(aFace)
			faces.append(aFace)
			areas.append(anArea)
		max_index = areas.index(max(areas))
		ext_boundary = faces[max_index]
		int_boundaries = list(set(faces) - set([ext_boundary]))
		int_wires = []
		for int_boundary in int_boundaries:
			temp_wires = []
			_ = int_boundary.Wires(None, temp_wires)
			int_wires.append(WireRemoveCollinearEdges.processItem(temp_wires[0], angTol))
		temp_wires = []
		_ = ext_boundary.Wires(None, temp_wires)
		ext_wire = WireRemoveCollinearEdges.processItem(temp_wires[0], 0.1)
		try:
			return topologic.Face.ByExternalInternalBoundaries(ext_wire, int_wires)
		except:
			return topologic.Face.ByExternalInternalBoundaries(planarize(ext_wire), planarizeList(int_wires))
	else:
		return None

def recur(input, angTol):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem, angTol))
	else:
		output = processItem([input, angTol])
	return output
	
class SvFaceByPlanarShell(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face from the input planar Shell   
	"""
	bl_idname = 'SvFaceByPlanarShell'
	bl_label = 'Face.ByPlanarShell'
	Level: IntProperty(name='Level', default =2,min=1, update = updateNode)
	AngTol: FloatProperty(name='AngTol', default=0.1, min=0, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Shell')
		self.inputs.new('SvStringsSocket', 'Level').prop_name='Level'
		self.inputs.new('SvStringsSocket', 'Angular Tolerance').prop_name='AngTol'
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		shellList = self.inputs['Shell'].sv_get(deepcopy=True)
		level = flatten(self.inputs['Level'].sv_get(deepcopy=False, default= 2))
		angTol = self.inputs['Angular Tolerance'].sv_get(deepcopy=False)[0][0]
		if isinstance(level,list):
			level = int(level[0])
		shellList = list(list_level_iter(shellList,level))
		shellList = [flatten(t) for t in shellList]
		outputs = []
		for t in range(len(shellList)):
			outputs.append(recur(shellList[t], angTol))
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceByPlanarShell)

def unregister():
	bpy.utils.unregister_class(SvFaceByPlanarShell)
