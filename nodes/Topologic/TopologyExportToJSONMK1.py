import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import json

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def repeat(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

# From https://stackoverflow.com/questions/34432056/repeat-elements-of-list-between-each-other-until-we-reach-a-certain-length
def onestep(cur,y,base):
    # one step of the iteration
    if cur is not None:
        y.append(cur)
        base.append(cur)
    else:
        y.append(base[0])  # append is simplest, for now
        base = base[1:]+[base[0]]  # rotate
    return base

def iterate(list):
	maxLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		for i in range(len(anItem), maxLength):
			anItem.append(None)
		y=[]
		base=[]
		for cur in anItem:
			base = onestep(cur,y,base)
			# print(base,y)
		returnList.append(y)
	return returnList

def trim(list):
	minLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength < minLength:
			minLength = newLength
	for anItem in list:
		anItem = anItem[:minLength]
		returnList.append(anItem)
	return returnList

# Adapted from https://stackoverflow.com/questions/533905/get-the-cartesian-product-of-a-series-of-lists
def interlace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in interlace(ar_list[1:]):
                yield [a,]+prod

def transposeList(l):
	length = len(l[0])
	returnList = []
	for i in range(length):
		tempRow = []
		for j in range(len(l)):
			tempRow.append(l[j][i])
		returnList.append(tempRow)
	return returnList

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

def getTopologyDictionary(topology):
	d = topology.GetDictionary()
	keys = d.Keys()
	returnDict = {}
	for key in keys:
		try:
			attr = d.ValueAtKey(key)
		except:
			raise Exception("Dictionary.Values - Error: Could not retrieve a Value at the specified key ("+key+")")
		if isinstance(attr, topologic.IntAttribute):
			returnDict[key] = (attr.IntValue())
		elif isinstance(attr, topologic.DoubleAttribute):
			returnDict[key] = (attr.DoubleValue())
		elif isinstance(attr, topologic.StringAttribute):
			returnDict[key] = (attr.StringValue())
		elif isinstance(attr, topologic.ListAttribute):
			returnDict[key] = (listAttributeValues(attr))
		else:
			returnDict[key]=("")
	return returnDict

def cellAperturesAndDictionaries(topology, tol):
	cells = []
	try:
		_ = topology.Cells(None, cells)
	except:
		return [[],[],[]]
	cellApertures = []
	cellDictionaries = []
	cellSelectors = []
	for aCell in cells:
		tempApertures = []
		_ = aCell.Apertures(tempApertures)
		for anAperture in tempApertures:
			cellApertures.append(anAperture)
		cellDictionary = getTopologyDictionary(aCell)
		if len(cellDictionary.keys()) > 0:
			cellDictionaries.append(cellDictionary)
			iv = topologic.CellUtility.InternalVertex(aCell, tol)
			cellSelectors.append([iv.X(), iv.Y(), iv.Z()])
	return [cellApertures, cellDictionaries, cellSelectors]

def faceAperturesAndDictionaries(topology, tol):
	faces = []
	try:
		_ = topology.Faces(None, faces)
	except:
		return [[],[],[]]
	faceApertures = []
	faceDictionaries = []
	faceSelectors = []
	for aFace in faces:
		tempApertures = []
		_ = aFace.Apertures(tempApertures)
		for anAperture in tempApertures:
			faceApertures.append(anAperture)
		faceDictionary = getTopologyDictionary(aFace)
		if len(faceDictionary.keys()) > 0:
			faceDictionaries.append(faceDictionary)
			iv = topologic.FaceUtility.InternalVertex(aFace, tol)
			faceSelectors.append([iv.X(), iv.Y(), iv.Z()])
	return [faceApertures, faceDictionaries, faceSelectors]

def edgeAperturesAndDictionaries(topology, tol):
	edges = []
	try:
		_ = topology.Edges(None, edges)
	except:
		return [[],[],[]]
	edgeApertures = []
	edgeDictionaries = []
	edgeSelectors = []
	for anEdge in edges:
		tempApertures = []
		_ = anEdge.Apertures(tempApertures)
		for anAperture in tempApertures:
			edgeApertures.append(anAperture)
		edgeDictionary = getTopologyDictionary(anEdge)
		if len(edgeDictionary.keys()) > 0:
			edgeDictionaries.append(edgeDictionary)
			iv = topologic.EdgeUtility.PointAtParameter(anEdge, 0.5)
			edgeSelectors.append([iv.X(), iv.Y(), iv.Z()])
	return [edgeApertures, edgeDictionaries, edgeSelectors]

def vertexAperturesAndDictionaries(topology, tol):
	vertices = []
	try:
		_ = topology.Vertices(None, vertices)
	except:
		return [[],[],[]]
	vertexApertures = []
	vertexDictionaries = []
	vertexSelectors = []
	for aVertex in vertices:
		tempApertures = []
		_ = aVertex.Apertures(tempApertures)
		for anAperture in tempApertures:
			vertexApertures.append(anAperture)
		vertexDictionary = getTopologyDictionary(aVertex)
		if len(vertexDictionary.keys()) > 0:
			vertexDictionaries.append(vertexDictionary)
			vertexSelectors.append([aVertex.X(), aVertex.Y(), aVertex.Z()])
	return [vertexApertures, vertexDictionaries, vertexSelectors]


def apertureDicts(apertureList):
	apertureDicts = []
	for anAperture in apertureList:
		apertureData = {}
		apertureData['brep'] = anAperture.String()
		apertureData['dictionary'] = getTopologyDictionary(anAperture)
		apertureDicts.append(apertureData)
	return apertureDicts

def subTopologyDicts(dicts, selectors):
	returnDicts = []
	for i in range(len(dicts)):
		data = {}
		data['dictionary'] = dicts[i]
		data['selector'] = selectors[i]
		returnDicts.append(data)
	return returnDicts

def getTopologyData(topology, tol):
	returnDict = {}
	brep = topology.String()
	dictionary = getTopologyDictionary(topology)
	returnDict['brep'] = brep
	returnDict['dictionary'] = dictionary
	cellApertures, cellDictionaries, cellSelectors = cellAperturesAndDictionaries(topology, tol)
	faceApertures, faceDictionaries, faceSelectors = faceAperturesAndDictionaries(topology, tol)
	edgeApertures, edgeDictionaries, edgeSelectors = edgeAperturesAndDictionaries(topology, tol)
	vertexApertures, vertexDictionaries, vertexSelectors = vertexAperturesAndDictionaries(topology, tol)
	returnDict['cellApertures'] = apertureDicts(cellApertures)
	returnDict['faceApertures'] = apertureDicts(faceApertures)
	returnDict['edgeApertures'] = apertureDicts(edgeApertures)
	returnDict['vertexApertures'] = apertureDicts(vertexApertures)
	returnDict['cellDictionaries'] = subTopologyDicts(cellDictionaries, cellSelectors)
	returnDict['faceDictionaries'] = subTopologyDicts(faceDictionaries, faceSelectors)
	returnDict['edgeDictionaries'] = subTopologyDicts(edgeDictionaries, edgeSelectors)
	returnDict['vertexDictionaries'] = subTopologyDicts(vertexDictionaries, vertexSelectors)
	return returnDict

def processItem(item, overwrite):
	topologyList = item[0]
	if not (isinstance(topologyList,list)):
		topologyList = [topologyList]
	filepath = item[1]
	tol = item[2]
	# Make sure the file extension is .json
	ext = filepath[len(filepath)-5:len(filepath)]
	if ext.lower() != ".json":
		filepath = filepath+".json"
	f = None
	try:
		if overwrite == True:
			f = open(filepath, "w")
		else:
			f = open(filepath, "x") # Try to create a new File
	except:
		raise Exception("Error: Could not create a new file at the following location: "+filepath)
	if (f):
		jsondata = []
		for topology in topologyList:
			jsondata.append(getTopologyData(topology, tol))
		json.dump(jsondata, f, indent=4, sort_keys=True)
		f.close()	
		return True
	return False

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvTopologyExportToJSONMK1(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Exports the input Topology to a JSON file   
	"""
	bl_idname = 'SvTopologyExportToJSONMK1'
	bl_label = 'Topology.ExportToJSON MK1'
	OverwriteProp: BoolProperty(name="Overwrite", default=True, update=updateNode)
	FilePath: StringProperty(name="file", default="", subtype="FILE_PATH")
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'File Path').prop_name='FilePath'
		self.inputs.new('SvStringsSocket', 'Overwrite File').prop_name = 'OverwriteProp'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Status')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		try:
			filepathList = self.inputs['File Path'].sv_get(deepcopy=True)
			filepathList = flatten(filepathList)
			topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		except:
			self.outputs['Status'].sv_set([False])
			return
		overwrite = self.inputs['Overwrite File'].sv_get(deepcopy=False)[0][0] #accept only one overwrite flag
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=False)
		toleranceList = flatten(toleranceList)

		inputs = [topologyList, filepathList, toleranceList]
		if ((self.Replication) == "Default" or (self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, overwrite))
		self.outputs['Status'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyExportToJSONMK1)

def unregister():
	bpy.utils.unregister_class(SvTopologyExportToJSONMK1)
