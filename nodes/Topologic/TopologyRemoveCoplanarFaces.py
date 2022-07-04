import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time

from . import TopologyClusterFaces, ShellByFaces, FaceByPlanarShell, Replication

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

def processItem(item):
	topology, angTol, tolerance = item
	t = topology.Type()
	if (t == 1) or (t == 2) or (t == 4) or (t == 8) or (t == 128):
		return topology
	clusters = TopologyClusterFaces.processItem([topology, tolerance])
	shells = []
	for aCluster in clusters:
		faces = []
		_ = aCluster.Faces(None, faces)
		shells.append(ShellByFaces.processItem((faces, tolerance)))
	faces = []
	print("SHELLS", shells)
	shells = Replication.flatten(shells)
	for aShell in shells:
		print("ASHELL", aShell)
		faces.append(FaceByPlanarShell.processItem([aShell, angTol]))
	returnTopology = None
	if t == 16:
		try:
			returnTopology = topologic.Shell.ByFaces(faces)
		except:
			returnTopology = topologic.Cluster.ByTopologies(faces)
	elif t == 32:
		try:
			returnTopology = topologic.Cell.ByFaces(faces)
		except:
			returnTopology = topologic.Cluster.ByTopologies(faces)
	elif t == 64:
		try:
			returnTopology = topologic.CellComplex.ByFaces(faces)
		except:
			returnTopology = topologic.Cluster.ByTopologies(faces)
	return returnTopology

def recur(input, angTol, tolerance):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem, angTol, tolerance))
	else:
		output = processItem([input, angTol, tolerance])
	return output

class SvTopologyRemoveCoplanarFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Removes any coplanar faces from the input Topology    
	"""
	bl_idname = 'SvTopologyRemoveCoplanarFaces'
	bl_label = 'Topology.RemoveCoplanarFaces'
	AngTol: FloatProperty(name='AngTol', default=0.1, min=0, precision=4, update=updateNode)
	Tol: FloatProperty(name='Tol', default=0.0001, min=0, precision=4, update=updateNode)
	Level: IntProperty(name='Level', default =2,min=1, update = updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Level').prop_name='Level'
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
		level = Replication.flatten(self.inputs['Level'].sv_get(deepcopy=False, default= 2))
		if isinstance(level,list):
			level = int(level[0])
		topologyList = list(list_level_iter(topologyList,level))
		topologyList = [Replication.flatten(t) for t in topologyList]
		outputs = []
		for t in range(len(topologyList)):
			outputs.append(recur(topologyList[t], angTol, tol))
		self.outputs['Topology'].sv_set(outputs)
		end = time.time()
		print("Topology.RemoveCoplanarFaces MK2 Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologyRemoveCoplanarFaces)

def unregister():
    bpy.utils.unregister_class(SvTopologyRemoveCoplanarFaces)
