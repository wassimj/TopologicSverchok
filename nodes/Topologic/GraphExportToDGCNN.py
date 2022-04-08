import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
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
		elif isinstance(attr, float) or isinstance(attr, int) or isinstance(attr, str) or isinstance(attr, dict):
			returnList.append(attr)
	return returnList

def valueAtKey(item, key):
	if isinstance(item, dict):
		attr = item[key]
	elif isinstance(item, topologic.Dictionary):
		attr = item.ValueAtKey(key)
	if isinstance(attr, topologic.IntAttribute):
		return (attr.IntValue())
	elif isinstance(attr, topologic.DoubleAttribute):
		return (attr.DoubleValue())
	elif isinstance(attr, topologic.StringAttribute):
		return (attr.StringValue())
	elif isinstance(attr, topologic.ListAttribute):
		return (listAttributeValues(attr))
	elif isinstance(attr, float) or isinstance(attr, int) or isinstance(attr, str):
		return attr
	elif isinstance(attr, list):
		return listAttributeValues(attr)
	elif isinstance(attr, dict):
		return attr
	else:
		return None

def vertexIndex(vertex, vertices):
	for i in range(len(vertices)):
		if topologic.Topology.IsSame(vertex, vertices[i]):
			return i
	return None

def vertexCategory(vertex):
	z = vertex.Z
	category = 0
	if z < 70:
		category = 0
	elif z < 120:
		category = 1
	else:
		category = 3
	return category

def graphVertices(graph):
	vertices = []
	if graph:
		try:
			_ = graph.Vertices(vertices)
		except:
			print("ERROR: (Topologic>Graph.Vertices) operation failed.")
			vertices = None
	if vertices:
		return vertices
	else:
		return []

def adjacentVertices(graph, vertex):
	vertices = []
	_ = graph.AdjacentVertices(vertex, vertices)
	return list(vertices)

def processItem(item):
	graph, label, key, filepath, overwrite = item
	vertices = graphVertices(graph)
	outputString = str(len(vertices))+" "+str(label)+"\n"
	for j in range(len(vertices)):
		d = vertices[j].GetDictionary()
		vLabel = valueAtKey(d, key)
		av = adjacentVertices(graph, vertices[j])
		outputString = outputString+str(vLabel)+" "+ str(len(av))+" "
		for k in range(len(av)):
			vi = vertexIndex(av[k], vertices)
			outputString = outputString+str(vi)+" "
		if j < len(vertices)-1:
			outputString = outputString+"\n"
	print(outputString)
	# Make sure the file extension is .txt
	ext = filepath[len(filepath)-4:len(filepath)]
	if ext.lower() != ".txt":
		filepath = filepath+".txt"
	f = None
	try:
		if overwrite == True:
			f = open(filepath, "w")
		else:
			f = open(filepath, "x") # Try to create a new File
	except:
		raise Exception("Error: Could not create a new file at the following location: "+filepath)
	if (f):
		f.write(outputString)
		f.close()	
		return True
	return False

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]
	
class SvGraphExportToDGCNN(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Exports the input Graph to a text file compatible with DGCNN
	"""
	bl_idname = 'SvGraphExportToDGCNN'
	bl_label = 'Graph.ExportToDGCNN'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Label: StringProperty(name='Graph Label', default="0", update=updateNode)
	Key: StringProperty(name='Vertex Label Key', default="ID", update=updateNode)
	OverwriteProp: BoolProperty(name="Overwrite", default=True, update=updateNode)
	FilePath: StringProperty(name="File Path", default="", subtype="FILE_PATH")

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Graph Label').prop_name='Label'
		self.inputs.new('SvStringsSocket', 'Vertex Label Key').prop_name='Key'
		self.inputs.new('SvStringsSocket', 'File Path').prop_name='FilePath'
		self.inputs.new('SvStringsSocket', 'Overwrite File').prop_name = 'OverwriteProp'
		self.outputs.new('SvStringsSocket', 'Status')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Status'].sv_set([])
			return
		graphList = self.inputs['Graph'].sv_get(deepcopy=True)
		labelList = self.inputs['Graph Label'].sv_get(deepcopy=True)
		keyList = self.inputs['Vertex Label Key'].sv_get(deepcopy=True)
		graphList = flatten(graphList)
		labelList = flatten(labelList)
		keyList = flatten(keyList)
		filepathList = self.inputs['File Path'].sv_get(deepcopy=True)
		filepathList = flatten(filepathList)
		overwriteList = self.inputs['Overwrite File'].sv_get(deepcopy=False)
		overwriteList = flatten(overwriteList)
		inputs = [graphList, labelList, keyList, filepathList, overwriteList]
		if ((self.Replication) == "Default"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		if ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Status'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvGraphExportToDGCNN)

def unregister():
	bpy.utils.unregister_class(SvGraphExportToDGCNN)
