import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic

def getValueAtKey(dict, key):
	returnValue = "None"
	try:
		returnValue = str((cppyy.bind_object(dict.ValueAtKey(key).Value(), "std::string")))
	except:
		returnValue = "None"
	return returnValue

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
			sourceType = source.GetType()
			type = str(sourceType)
			if sourceType == topologic.Vertex.Type():
				sourceSelector = source
			elif sourceType == topologic.Edge.Type():
				sourceSelector = topologic.EdgeUtility.PointAtParameter(source, 0.5)
			elif sourceType == topologic.Face.Type():
				sourceSelector = topologic.FaceUtility.InternalVertex(source)
			elif sourceType == topologic.Cell.Type():
				sourceSelector = topologic.CellUtility.InternalVertex(source)
			elif sourceType == topologic.CellComplex.Type():
				sourceSelector = source.Centroid()
			x = "{:.4f}".format(sourceSelector.X())
			y = "{:.4f}".format(sourceSelector.Y())
			z = "{:.4f}".format(sourceSelector.Z())
			copyKeys = stl_keys.__class__(stl_keys) #wlav suggested workaround. Make a copy first
			stl_keys = [str((copyKeys.front(), copyKeys.pop_front())[0]) for x in copyKeys]
			for aSourceKey in stl_keys:
				if sourceKeys == "":
					sourceKeys = aSourceKey
				else:
					sourceKeys = sourceKeys+"|"+aSourceKey
				aSourceValue = getValueAtKey(d, aSourceKey)
				if sourceValues == "":
					sourceValues = aSourceValue
				else:
					sourceValues = sourceValues+"|"+aSourceValue

			returnList.append(type+","+x+","+y+","+z+","+sourceKeys+","+sourceValues)
	return returnList

def processItem(topology):
	finalList = []
	for anItem in topology:
		itemType = anItem.GetType()
		if itemType == topologic.CellComplex.Type():
			finalList = finalList + (dictionaryString([anItem]))
			cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
			_ = anItem.Cells(cells)
			finalList = finalList + (dictionaryString(cells))
			faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
			_ = anItem.Faces(faces)
			finalList = finalList + (dictionaryString(faces))
			edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = anItem.Edges(edges)
			finalList = finalList + (dictionaryString(edges))
			vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			_ = anItem.Vertices(vertices)
			finalList = finalList + (dictionaryString(vertices))
		if itemType == topologic.Cell.Type():
			finalList = finalList + (dictionaryString([anItem]))
			faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
			_ = anItem.Faces(faces)
			finalList = finalList + (dictionaryString(faces))
			edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = anItem.Edges(edges)
			finalList = finalList + (dictionaryString(edges))
			vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			_ = anItem.Vertices(vertices)
			finalList = finalList + (dictionaryString(vertices))
		if itemType == topologic.Face.Type():
			finalList = finalList + (dictionaryString([anItem]))
			edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = anItem.Edges(edges)
			finalList = finalList + (dictionaryString(edges))
			vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			_ = anItem.Vertices(vertices)
			finalList = finalList + (dictionaryString(vertices))
		if itemType == topologic.Edge.Type():
			finalList = finalList + (dictionaryString([anItem]))
			vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			_ = anItem.Vertices(vertices)
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
