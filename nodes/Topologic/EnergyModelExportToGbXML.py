import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from os.path import exists
try:
	import openstudio
except:
	raise Exception("Error: Could not import openstudio.")
import os

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

def processItem(item, overwrite):
	osModel = item[0]
	filepath = item[1]
	# Make sure the file extension is .xml
	ext = filepath[len(filepath)-4:len(filepath)]
	if ext.lower() != ".xml":
		filepath = filepath+".xml"
	if(exists(filepath) and (overwrite == False)):
		raise Exception("Error: Could not create a new file at the following location: "+filepath)
	return openstudio.gbxml.GbXMLForwardTranslator().modelToGbXML(osModel, openstudio.openstudioutilitiescore.toPath(filepath))

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvEnergyModelExportToGbXML(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Exports the input Energy Model to a gbXML file   
	"""
	bl_idname = 'SvEnergyModelExportToGbXML'
	bl_label = 'EnergyModel.ExportToGbXML'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	OverwriteProp: BoolProperty(name="Overwrite", default=True, update=updateNode)
	FilePath: StringProperty(name="file", default="", subtype="FILE_PATH")

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Energy Model')
		self.inputs.new('SvStringsSocket', 'File Path').prop_name='FilePath'
		self.inputs.new('SvStringsSocket', 'Overwrite File').prop_name = 'OverwriteProp'
		self.outputs.new('SvStringsSocket', 'Status')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		try:
			modelList = self.inputs['Energy Model'].sv_get(deepcopy=True)
			filePathList = self.inputs['File Path'].sv_get(deepcopy=True)
			modelList = flatten(modelList)
			filePathList = flatten(filePathList)
		except:
			self.outputs['Status'].sv_set([False])
			return
		overwrite = self.inputs['Overwrite File'].sv_get(deepcopy=True)[0][0] #accept only one overwrite flag
		inputs = [modelList, filePathList]
		if ((self.Replication) == "Default"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Trim"):
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
			outputs.append(processItem(anInput, overwrite))
		self.outputs['Status'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEnergyModelExportToGbXML)

def unregister():
	bpy.utils.unregister_class(SvEnergyModelExportToGbXML)
