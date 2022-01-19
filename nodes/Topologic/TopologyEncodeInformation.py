import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("DictionaryByKeysValues - Keys and Values do not have the same length")
	stl_keys = []
	stl_values = []
	for i in range(len(keys)):
		if isinstance(keys[i], str):
			stl_keys.append(keys[i])
		else:
			stl_keys.append(str(keys[i]))
		if isinstance(values[i], list) and len(values[i]) == 1:
			value = values[i][0]
		else:
			value = values[i]
		if isinstance(value, bool):
			if value == False:
				stl_values.append(topologic.IntAttribute(0))
			else:
				stl_values.append(topologic.IntAttribute(1))
		elif isinstance(value, int):
			stl_values.append(topologic.IntAttribute(value))
		elif isinstance(value, float):
			stl_values.append(topologic.DoubleAttribute(value))
		elif isinstance(value, str):
			stl_values.append(topologic.StringAttribute(value))
		elif isinstance(value, list):
			l = []
			for v in value:
				if isinstance(v, bool):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, int):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, float):
					l.append(topologic.DoubleAttribute(v))
				elif isinstance(v, str):
					l.append(topologic.StringAttribute(v))
			stl_values.append(topologic.ListAttribute(l))
		else:
			raise Exception("Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
	myDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
	return myDict


def topologyContains(topology, vertex, tolerance):
	contains = False
	if topology.Type() == topologic.Vertex.Type():
		try:
			contains = (topologic.VertexUtility.Distance(topology, vertex) <= tolerance)
		except:
			contains = False
		return contains
	elif topology.Type() == topologic.Edge.Type():
		try:
			_ = topologic.EdgeUtility.ParameterAtPoint(topology, vertex)
			contains = True
		except:
			contains = False
		return contains
	elif topology.Type() == topologic.Face.Type():
		return topologic.FaceUtility.IsInside(topology, vertex, tolerance)
	elif topology.Type() == topologic.Cell.Type():
		return (topologic.CellUtility.Contains(topology, vertex, tolerance) == 0)
	return contains

def listAttributeValues(listAttribute):
	listAttributes = listAttribute.ListValue()
	returnList = []
	for attr in listAttributes:
		if isinstance(attr, topologic.IntAttribute):
			returnList.append(attr.IntValue())
		elif isinstance(attr, topologic.DoubleAttribute):
			returnList.append(attr.DoubleValue())
		elif isinstance(attr, topologic.StringAttribute):
			returnList.append(attr.StringValue())
	return returnList

def getValueAtKey(item, key):
	try:
		attr = item.ValueAtKey(key)
	except:
		raise Exception("Dictionary.ValueAtKey - Error: Could not retrieve a Value at the specified key ("+key+")")
	if isinstance(attr, topologic.IntAttribute):
		return (attr.IntValue())
	elif isinstance(attr, topologic.DoubleAttribute):
		return (attr.DoubleValue())
	elif isinstance(attr, topologic.StringAttribute):
		return (attr.StringValue())
	elif isinstance(attr, topologic.ListAttribute):
		return (listAttributeValues(attr))
	else:
		return None

def transferDictionaries(selectors, dictionaries, topologyType, topology, tolerance):
	if topologyType == topologic.Vertex.Type():
		if topology.Type() == topologic.Vertex.Type():
			sinks = [topology]
		else:
			sinks = []
			_ = topology.Vertices(None, sinks)
	elif topologyType == topologic.Edge.Type():
		if topology.Type() == topologic.Edge.Type():
			sinks = [topology]
		else:
			sinks = []
			_ = topology.Edges(None, sinks)
	elif topologyType == topologic.Face.Type():
		if topology.Type() == topologic.Face.Type():
			sinks = [topology]
		else:
			sinks = []
			_ = topology.Faces(None, sinks)
	elif topologyType == topologic.Cell.Type():
		if topology.Type() == topologic.Cell.Type():
			sinks = [topology]
		else:
			sinks = []
			_ = topology.Cells(None, sinks)
	else:
		sinks = []
	for i in range(len(selectors)):
		selector = selectors[i]
		if selector == None:
			continue
		d = dictionaries[i]
		if d == None:
			continue
		sourceKeys = d.Keys()
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
					k = sourceKeys[j]
					sourceValue = str(getValueAtKey(d, k))
					if sourceValue != None:
						if sinkValues[index] != "":
							sinkValues[index] = sinkValues[index]+","+sourceValue
						else:
							sinkValues[index] = sourceValue
				if len(sinkKeys) > 0 and len(sinkValues) > 0:
					newDict = processKeysValues(sinkKeys, sinkValues)
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
		selectors = []
		selectors.append(v)
		keys = columns[4].split("|",1024)
		values = columns[5].split("|",1024)
		d = processKeysValues(keys, values)
		dictionaries = []
		dictionaries.append(d)
		topology = transferDictionaries(selectors, dictionaries, topologyType, topology, tolerance)
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
