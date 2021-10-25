import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic

def dictionaryByKeysValues(keys, values):
	stl_keys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
	stl_values = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
	for aKey in keys:
		stl_keys.push_back(aKey)
	for aValue in values:
		stl_values.push_back(topologic.StringAttribute(aValue))
	return topologic.Dictionary.ByKeysValues(stl_keys, stl_values)

def topologyContains(topology, vertex, tolerance):
	contains = False
	if topology.GetType() == topologic.Vertex.Type():
		try:
			contains = (topologic.VertexUtility.Distance(topology, vertex) <= tolerance)
		except:
			contains = False
		return contains
	elif topology.GetType() == topologic.Edge.Type():
		try:
			_ = topologic.EdgeUtility.ParameterAtPoint(topology, vertex)
			contains = True
		except:
			contains = False
		return contains
	elif topology.GetType() == topologic.Face.Type():
		return topologic.FaceUtility.IsInside(topology, vertex, tolerance)
	elif topology.GetType() == topologic.Cell.Type():
		return (topologic.CellUtility.Contains(topology, vertex, tolerance) == 0)
	return contains

def getValueAtKey(dict, key):
	returnValue = None
	try:
		returnValue = str((cppyy.bind_object(dict.ValueAtKey(key).Value(), "std::string")))
	except:
		returnValue = None
	return returnValue

def transferDictionaries(selectors, dictionaries, topologyType, topology, tolerance):
	if topologyType == topologic.Vertex.Type():
		sinks = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		_ = topology.Vertices(sinks)
	elif topologyType == topologic.Edge.Type():
		sinks = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		_ = topology.Vertices(sinks)
	elif topologyType == topologic.Face.Type():
		sinks = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = topology.Vertices(sinks)
	elif topologyType == topologic.Cell.Type():
		sinks = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		_ = topology.Cells(sinks)
	else:
		sinks = []
	for i in range(len(selectors)):
		selector = selectors[i]
		if selector == None:
			continue
		d = dictionaries[i]
		if d == None:
			continue
		stl_keys = d.Keys()
		if len(stl_keys) == 0:
			continue
		copyKeys = stl_keys.__class__(stl_keys) #wlav suggested workaround. Make a copy first
		sourceKeys = [str((copyKeys.front(), copyKeys.pop_front())[0]) for x in copyKeys]
		sinkKeys = []
		sinkValues = []
		for sink in sinks:
			if topologyContains(sink, selector, tolerance):
				for aSourceKey in sourceKeys:
					if aSourceKey not in sinkKeys:
						sinkKeys.append(aSourceKey)
						sinkValues.append("")
				for j in range(len(sourceKeys)):
					index = sinkKeys.index(sourceKeys[j])
					k = cppyy.gbl.std.string(sourceKeys[j])
					sourceValue = getValueAtKey(d, k)
					if sourceValue != None:
						if sinkValues[index] != "":
							sinkValues[index] = sinkValues[index]+","+sourceValue
						else:
							sinkValues[index] = sourceValue
				if len(sinkKeys) > 0 and len(sinkValues) > 0:
					newDict = dictionaryByKeysValues(sinkKeys, sinkValues)
					_ = sink.SetDictionary(newDict)
	return topology

def processItem(topology, csv_string, tolerance):
	rows = csv_string.split("\n",50000)
	for row in rows:
		if row == "": #Ignore empty lines
			continue
		if row[0].isdigit() == False: # Ignore header
			continue
		columns = row.split(",",6)
		topologyType = int(columns[0])
		x = float(columns[1])
		y = float(columns[2])
		z = float(columns[3])
		v = topologic.Vertex.ByCoordinates(x,y,z)
		selectors = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
		selectors.push_back(v)
		keys = columns[4].split("|",1024)
		values = columns[5].split("|",1024)
		d = dictionaryByKeysValues(keys, values)
		dictionaries = cppyy.gbl.std.list[topologic.Dictionary]()
		dictionaries.push_back(d)
		#topology = topology.SetDictionaries(selectors, dictionaries, topologyType)
		topology = transferDictionaries(list(selectors), list(dictionaries), topologyType, topology, tolerance)
	return topology

class SvTopologyEncodeInformation(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Embeds the Dictionaries derived from the input CSV data into the input Topology
	"""
	bl_idname = 'SvTopologyEncodeInformation'
	bl_label = 'Topology.EncodeInformation'
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'CSV String')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name='Tolerance'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topology = self.inputs['Topology'].sv_get(deepcopy=False)[0]
		csv_string = self.inputs['CSV String'].sv_get(deepcopy=False)[0]
		tolerance = self.inputs['Tolerance'].sv_get(deepcopy=False)[0][0]
		topology = processItem(topology, csv_string, tolerance)
		self.outputs['Topology'].sv_set([topology])

def register():
    bpy.utils.register_class(SvTopologyEncodeInformation)

def unregister():
    bpy.utils.unregister_class(SvTopologyEncodeInformation)
