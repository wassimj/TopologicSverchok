import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic
import cppyy

def dictionaryByKeysValues(keys, values):
	stl_keys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
	stl_values = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
	for aKey in keys:
		stl_keys.push_back(aKey)
	for aValue in values:
		stl_values.push_back(topologic.StringAttribute(aValue))
	return topologic.Dictionary.ByKeysValues(stl_keys, stl_values)

def processItem(item, topology):
	topologyType = int(item[0])
	x = item[1]
	y = item[2]
	z = item[3]
	print(topologyType)
	print([x,y,z])
	v = topologic.Vertex.ByCoordinates(x,y,z)
	selectors = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	selectors.push_back(v)
	keys = item[4].split("|",1024)
	values = item[5].split("|",1024)
	d = dictionaryByKeysValues(keys, values)
	dictionaries = cppyy.gbl.std.list[topologic.Dictionary]()
	dictionaries.push_back(d)
	return topology.SetDictionaries(selectors, dictionaries, topologyType)


class SvTopologyEncodeInformation(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates Dictionaries, Selectors, and Type Filters from the input CSV data   
	"""
	bl_idname = 'SvTopologyEncodeInformation'
	bl_label = 'Topology.EncodeInformation'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=0, precision=4, update=updateNode)
	lacing: EnumProperty(name='Lacing', items=list_match_modes, default='REPEAT', update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Topology Type')
		self.inputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.inputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.inputs.new('SvStringsSocket', 'Z').prop_name = 'Z'
		self.inputs.new('SvStringsSocket', 'Keys')
		self.inputs.new('SvStringsSocket', 'Values')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topology = self.inputs['Topology'].sv_get(deepcopy=False)[0]
		topologyTypes = self.inputs['Topology Type'].sv_get(deepcopy=False)[0]
		xCoords = self.inputs['X'].sv_get(deepcopy=False)[0]
		yCoords = self.inputs['Y'].sv_get(deepcopy=False)[0]
		zCoords = self.inputs['Z'].sv_get(deepcopy=False)[0]
		keys = self.inputs['Keys'].sv_get(deepcopy=False)[0]
		values = self.inputs['Values'].sv_get(deepcopy=False)[0]
		maxLength = max([len(topologyTypes), len(xCoords), len(yCoords), len(zCoords), len(keys), len(values)])
		for i in range(len(topologyTypes), maxLength):
			topologyTypes.append(topologyTypes[-1])
		for i in range(len(xCoords), maxLength):
			xCoords.append(xCoords[-1])
		for i in range(len(yCoords), maxLength):
			yCoords.append(yCoords[-1])
		for i in range(len(zCoords), maxLength):
			zCoords.append(zCoords[-1])
		for i in range(len(keys), maxLength):
			keys.append(keys[-1])
		for i in range(len(values), maxLength):
			values.append(values[-1])
		if (len(xCoords) == len(yCoords) == len(zCoords)):
			inputs = zip(topologyTypes, xCoords, yCoords, zCoords, keys, values)
			for anInput in inputs:
				topology = processItem(anInput, topology)
			self.outputs['Topology'].sv_set([topology])

def register():
    bpy.utils.register_class(SvTopologyEncodeInformation)

def unregister():
    bpy.utils.unregister_class(SvTopologyEncodeInformation)
