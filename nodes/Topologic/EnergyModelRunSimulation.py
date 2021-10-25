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



def processItem(item):
    model = item[0]
    weatherFile = item[1]
    osBinaryPath = item[2]
    outputFolder = item[3]
    run = item[4]
    if not run:
        return None
    utcnow = datetime.utcnow()
    timestamp = utcnow.strftime("UTC-%Y-%m-%d-%H-%M-%S")
    outputFolder = os.path.join(outputFolder, timestamp)
    os.mkdir(outputFolder)
    osmPath = outputFolder + "/" + model.getBuilding().name().get() + ".osm"
    model.save(openstudio.openstudioutilitiescore.toPath(osmPath), True)
    oswPath = os.path.join(outputFolder, model.getBuilding().name().get() + ".osw")
    print("oswPath = "+oswPath)
    workflow = model.workflowJSON()
    workflow.setSeedFile(openstudio.openstudioutilitiescore.toPath(osmPath))
    print("Seed File Set")
    workflow.setWeatherFile(openstudio.openstudioutilitiescore.toPath(weatherFile))
    print("Weather File Set")
    workflow.saveAs(openstudio.openstudioutilitiescore.toPath(oswPath))
    print("OSW File Saved")
    cmd = osBinaryPath+" run -w " + "\"" + oswPath + "\""
    os.system(cmd)
    print("Simulation DONE")
    sqlPath = os.path.join(os.path.join(outputFolder,"run"), "eplusout.sql")
    print("sqlPath = "+sqlPath)
    osSqlFile = openstudio.SqlFile(openstudio.openstudioutilitiescore.toPath(sqlPath))
    model.setSqlFile(osSqlFile)
    return model

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvEnergyModelRunSimulation(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Topologic
    Tooltip: Runs an EnergyPlus simulation from the input energy model
    """
    bl_idname = 'SvEnergyModelRunSimulation'
    bl_label = 'EnergyModel.RunSimulation'
    Run: BoolProperty(name="Run", default=False, update=updateNode)
    Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Energy Model')
        self.inputs.new('SvStringsSocket', 'Weather File Path')
        self.inputs.new('SvStringsSocket', 'OpenStudio Binary Path')
        self.inputs.new('SvStringsSocket', 'Output Folder')
        self.inputs.new('SvStringsSocket', 'Run').prop_name = 'Run'
        self.outputs.new('SvStringsSocket', 'Energy Model')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Replication",text="")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        modelList = self.inputs['Energy Model'].sv_get(deepcopy=True)
        weatherFileList = self.inputs['Weather File Path'].sv_get(deepcopy=True)
        osBinaryPathList = self.inputs['OpenStudio Binary Path'].sv_get(deepcopy=True)
        outputFolderList = self.inputs['Output Folder'].sv_get(deepcopy=True)
        runList = self.inputs['Run'].sv_get(deepcopy=True)

        modelList = flatten(modelList)
        weatherFileList = flatten(weatherFileList)
        osBinaryPathList = flatten(osBinaryPathList)
        outputFolderList = flatten(outputFolderList)
        runList = flatten(runList)

        inputs = [modelList, weatherFileList, osBinaryPathList, outputFolderList, runList]
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
        self.outputs['Energy Model'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvEnergyModelRunSimulation)

def unregister():
    bpy.utils.unregister_class(SvEnergyModelRunSimulation)
