import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

try:
	import openstudio
except:
	raise Exception("Error: Could not import openstudio.")
from datetime import datetime
import os
import subprocess
from subprocess import Popen, PIPE

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

def doubleValueFromQuery(sqlFile, EPReportName, EPReportForString, EPTableName, EPColumnName, EPRowName, EPUnits):
    doubleValue = 0.0
    query = "SELECT Value FROM tabulardatawithstrings WHERE ReportName='" + EPReportName + "' AND ReportForString='" + EPReportForString + "' AND TableName = '" + EPTableName + "' AND RowName = '" + EPRowName + "' AND ColumnName= '" + EPColumnName + "' AND Units='" + EPUnits + "'";
    osOptionalDoubleValue = sqlFile.execAndReturnFirstDouble(query)
    if (osOptionalDoubleValue.is_initialized()):
        doubleValue = osOptionalDoubleValue.get()
    else:
        raise Exception("Failed to get a double value from the SQL file.")
    return doubleValue

def processItem(item):
    model = item[0]
    EPReportName = item[1]
    EPReportForString = item[2]
    EPTableName = item[3]
    EPColumnName = item[4]
    EPRowName = item[5]
    EPUnits = item[6]
    sqlFile = model.sqlFile().get()
    doubleValue = doubleValueFromQuery(sqlFile, EPReportName, EPReportForString, EPTableName, EPColumnName, EPRowName, EPUnits)
    return doubleValue

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvEnergyModelQuery(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Topologic
    Tooltip: Query results from the input energy model
    """
    bl_idname = 'SvEnergyModelQuery'
    bl_label = 'EnergyModel.Query'
    Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
    EPReportName: StringProperty(name='EPReportName', default="HVACSizingSummary",update=updateNode)
    EPReportForString: StringProperty(name='EPReportForString', default="Entire Facility",update=updateNode)
    EPTableName: StringProperty(name='EPTableName', default="Zone Sensible Cooling",update=updateNode)
    EPColumnName: StringProperty(name='EPColumnName', default="Calculated Design Load",update=updateNode)
    EPUnits: StringProperty(name='EPUnits', default="W",update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Energy Model')
        self.inputs.new('SvStringsSocket', 'EPReportName').prop_name = 'EPReportName'
        self.inputs.new('SvStringsSocket', 'EPReportForString').prop_name = 'EPReportForString'
        self.inputs.new('SvStringsSocket', 'EPTableName').prop_name = 'EPTableName'
        self.inputs.new('SvStringsSocket', 'EPColumnName').prop_name = 'EPColumnName'
        self.inputs.new('SvStringsSocket', 'EPRowName')
        self.inputs.new('SvStringsSocket', 'EPUnits').prop_name = 'EPUnits'
        self.outputs.new('SvStringsSocket', 'Values')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Replication",text="")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        modelList = self.inputs['Energy Model'].sv_get(deepcopy=True)
        EPReportNameList = self.inputs['EPReportName'].sv_get(deepcopy=True)
        EPReportForStringList = self.inputs['EPReportForString'].sv_get(deepcopy=True)
        EPTableNameList = self.inputs['EPTableName'].sv_get(deepcopy=True)
        EPColumnNameList = self.inputs['EPColumnName'].sv_get(deepcopy=True)
        EPRowNameList = self.inputs['EPRowName'].sv_get(deepcopy=True)
        EPUnitsList = self.inputs['EPUnits'].sv_get(deepcopy=True)

        modelList = flatten(modelList)
        EPReportNameList = flatten(EPReportNameList)
        EPReportForStringList = flatten(EPReportForStringList)
        EPTableNameList = flatten(EPTableNameList)
        EPColumnNameList = flatten(EPColumnNameList)
        EPRowNameList = flatten(EPRowNameList)
        EPUnitsList = flatten(EPUnitsList)

        inputs = [modelList, EPReportNameList, EPReportForStringList, EPTableNameList, EPColumnNameList, EPRowNameList, EPUnitsList]
        outputs = []
        if ((self.Replication) == "Default"):
            inputs = repeat(inputs)
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
        for anInput in inputs:
            outputs.append(processItem(anInput))
        self.outputs['Values'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvEnergyModelQuery)

def unregister():
    bpy.utils.unregister_class(SvEnergyModelQuery)
