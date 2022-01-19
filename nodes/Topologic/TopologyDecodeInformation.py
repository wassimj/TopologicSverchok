import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic

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

def dictionaryString(sources):
	returnList = []
	for source in sources:
		type = ""
		x = ""
		y = ""
		z = ""
		sourceKeys = ""
		sourceValues = ""
		d = source.GetDictionary()
		if d == None:
			continue
		stl_keys = d.Keys()
		if len(stl_keys) > 0:
			sourceType = source.Type()
			type = str(sourceType)
			if sourceType == topologic.Vertex.Type():
				sourceSelector = source
			elif sourceType == topologic.Edge.Type():
				sourceSelector = topologic.EdgeUtility.PointAtParameter(source, 0.5)
			elif sourceType == topologic.Face.Type():
				sourceSelector = topologic.FaceUtility.InternalVertex(source, 0.0001)
			elif sourceType == topologic.Cell.Type():
				sourceSelector = topologic.CellUtility.InternalVertex(source, 0.0001)
			elif sourceType == topologic.CellComplex.Type():
				sourceSelector = source.Centroid()
			x = "{:.4f}".format(sourceSelector.X())
			y = "{:.4f}".format(sourceSelector.Y())
			z = "{:.4f}".format(sourceSelector.Z())
			for aSourceKey in stl_keys:
				if sourceKeys == "":
					sourceKeys = aSourceKey
				else:
					sourceKeys = sourceKeys+"|"+aSourceKey
				aSourceValue = str(getValueAtKey(d, aSourceKey))
				if sourceValues == "":
					sourceValues = aSourceValue
				else:
					sourceValues = sourceValues+"|"+aSourceValue

			returnList.append(type+","+x+","+y+","+z+","+sourceKeys+","+sourceValues)
	return returnList

def processItem(topology):
	finalList = []
	for anItem in topology:
		itemType = anItem.Type()
		if itemType == topologic.CellComplex.Type():
			finalList = finalList + (dictionaryString([anItem]))
			cells = []
			_ = anItem.Cells(None, cells)
			finalList = finalList + (dictionaryString(cells))
			faces = []
			_ = anItem.Faces(None, faces)
			finalList = finalList + (dictionaryString(faces))
			edges = []
			_ = anItem.Edges(None, edges)
			finalList = finalList + (dictionaryString(edges))
			vertices = []
			_ = anItem.Vertices(None, vertices)
			finalList = finalList + (dictionaryString(vertices))
		if itemType == topologic.Cell.Type():
			finalList = finalList + (dictionaryString([anItem]))
			faces = []
			_ = anItem.Faces(None, faces)
			finalList = finalList + (dictionaryString(faces))
			edges = []
			_ = anItem.Edges(None, edges)
			finalList = finalList + (dictionaryString(edges))
			vertices = []
			_ = anItem.Vertices(None, vertices)
			finalList = finalList + (dictionaryString(vertices))
		if itemType == topologic.Face.Type():
			finalList = finalList + (dictionaryString([anItem]))
			edges = []
			_ = anItem.Edges(None, edges)
			finalList = finalList + (dictionaryString(edges))
			vertices = []
			_ = anItem.Vertices(None, vertices)
			finalList = finalList + (dictionaryString(vertices))
		if itemType == topologic.Edge.Type():
			finalList = finalList + (dictionaryString([anItem]))
			vertices = []
			_ = anItem.Vertices(None, vertices)
			finalList = finalList + (dictionaryString(vertices))
		if itemType == topologic.Vertex.Type():
			finalList = finalList + (dictionaryString([anItem]))
	finalString = ""
	for i in range(len(finalList)):
		if i == len(finalList) - 1:
			finalString = finalString+finalList[i]
		else:
			finalString = finalString+finalList[i]+'\n'
	return finalString

class SvTopologyDecodeInformation(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Dictionaries, Selectors, and Type Filters of the input Topology to a CSV String   
	"""
	bl_idname = 'SvTopologyDecodeInformation'
	bl_label = 'Topology.DecodeInformation'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'CSV String')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topology = self.inputs['Topology'].sv_get(deepcopy=False)
		self.outputs['CSV String'].sv_set([processItem(topology)])

def register():
    bpy.utils.register_class(SvTopologyDecodeInformation)

def unregister():
    bpy.utils.unregister_class(SvTopologyDecodeInformation)
