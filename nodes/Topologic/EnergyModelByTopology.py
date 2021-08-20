# Based on code kindly provided by Adrià González Esteve
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import openstudio
import topologic
import cppyy
import math

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

def processItem(item):
	x = item[0]
	y = item[1]
	z = item[2]
	vert = None
	try:
		vert = topologic.Vertex.ByCoordinates(x, y, z)
	except:
		vert = None
	return vert

def getSubTopologies(topology, subTopologyClass):
    pointer = subTopologyClass.Ptr
    values = cppyy.gbl.std.list[pointer]()
    if subTopologyClass == topologic.Vertex:
        _ = topology.Vertices(values)
    elif subTopologyClass == topologic.Edge:
        _ = topology.Edges(values)
    elif subTopologyClass == topologic.Wire:
        _ = topology.Wires(values)
    elif subTopologyClass == topologic.Face:
        _ = topology.Faces(values)
    elif subTopologyClass == topologic.Shell:
        _ = topology.Shells(values)
    elif subTopologyClass == topologic.Cell:
        _ = topology.Cells(values)
    elif subTopologyClass == topologic.CellComplex:
        _ = topology.CellComplexes(values)
    return list(values)

def valueAtKey(dict, key):
    fv = None
    try:
        v = dict.ValueAtKey(key).Value()
    except:
        print("Error: Could not retrieve a Value at the specified key ("+key+")")
        return None
    if (isinstance(v, int) or (isinstance(v, float))):
        fv = v
    elif (isinstance(v, cppyy.gbl.std.string)):
        fv = v.c_str()
    else:
        resultList = []
        for i in v:
            if isinstance(i.Value(), cppyy.gbl.std.string):
                resultList.append(i.Value().c_str())
            else:
                resultList.append(i.Value())
        fv = resultList
    return fv

def processItem(item):
    '''
    building = topologic.Topology.ByString(open("C:/Users/wassi/osmFiles/TopologicBuilding.brep", "r").read())
    shadingSurfaces = topologic.Topology.ByString(open("C:/Users/wassi/osmFiles/TopologicShadingSurfaces.brep", "r").read())
    floorLevels = list(range(0, 70, 10))
    buildingName = "Multi-Storey Building"
    buildingType = "Commercial"
    defaultSpaceType = "189.1-2009 - Office - WholeBuilding - Md Office - CZ4-8"
    northAxis = 0
    glazingRatio = 0.4
    coolingTemp = 25.0
    heatingTemp = 20.0
    weatherFilePath = "C:/Users/wassi/osmFiles/GBR_London.Gatwick.037760_IWEC.epw"
    designDayFilePath = "C:/Users/wassi/osmFiles/GBR_London.Gatwick.037760_IWEC.ddy"
    openStudioTemplatePath = "C:/Users/wassi/osmFiles/OSMTemplate-OfficeBuilding-3.2.0.osm"
    '''

    #osModel = openstudio.model.Model.load(openstudio.toPath(openStudioTemplatePath)).get()

    osModel = item[0]
    weatherFilePath = item[1]
    designDayFilePath = item[2]
    building = item[3]
    shadingSurfaces = item[4]
    floorLevels = item[5]
    buildingName = item[6]
    buildingType = item[7]
    defaultSpaceType = item[8]
    northAxis = item[9]
    glazingRatio = item[10]
    coolingTemp = item[11]
    heatingTemp = item[12]

    osEPWFile = openstudio.openstudioutilitiesfiletypes.EpwFile.load(openstudio.toPath(weatherFilePath)).get()
    openstudio.model.WeatherFile.setWeatherFile(osModel, osEPWFile)
    ddyModel = openstudio.openstudioenergyplus.loadAndTranslateIdf(openstudio.toPath(designDayFilePath)).get()

    for ddy in ddyModel.getObjectsByType(openstudio.IddObjectType("OS:SizingPeriod:DesignDay")):
        osModel.addObject(ddy.clone())

    osBuilding = osModel.getBuilding()
    osBuilding.setStandardsNumberOfStories(len(floorLevels) - 1)
    osBuilding.setNominalFloortoFloorHeight(max(floorLevels) / osBuilding.standardsNumberOfStories().get())
    osBuilding.setDefaultConstructionSet(osModel.getDefaultConstructionSets()[0])
    osBuilding.setDefaultScheduleSet(osModel.getDefaultScheduleSets()[0])
    osBuilding.setName(buildingName)
    osBuilding.setStandardsBuildingType(buildingType)
    osBuilding.setSpaceType(osModel.getSpaceTypeByName(defaultSpaceType).get())
    for storyNumber in range(osBuilding.standardsNumberOfStories().get()):
        osBuildingStory = openstudio.model.BuildingStory(osModel)
        osBuildingStory.setName("STORY_" + str(storyNumber))
        osBuildingStory.setNominalZCoordinate(floorLevels[storyNumber])
        osBuildingStory.setNominalFloortoFloorHeight(osBuilding.nominalFloortoFloorHeight().get())
    osBuilding.setNorthAxis(northAxis)

    heatingScheduleConstant = openstudio.model.ScheduleConstant(osModel)
    heatingScheduleConstant.setValue(heatingTemp)
    coolingScheduleConstant = openstudio.model.ScheduleConstant(osModel)
    coolingScheduleConstant.setValue(coolingTemp)
    osThermostat = openstudio.model.ThermostatSetpointDualSetpoint(osModel)
    osThermostat.setHeatingSetpointTemperatureSchedule(heatingScheduleConstant)
    osThermostat.setCoolingSetpointTemperatureSchedule(coolingScheduleConstant)

    osBuildingStorys = list(osModel.getBuildingStorys())
    osBuildingStorys.sort(key=lambda x: x.nominalZCoordinate().get())
    osSpaces = []
    for spaceNumber, buildingCell in enumerate(getSubTopologies(building, topologic.Cell)):
        osSpace = openstudio.model.Space(osModel)
        osSpaceZ = buildingCell.CenterOfMass().Z()
        cellDictionary = buildingCell.GetDictionary()
        if cellDictionary:
            osSpaceTypeName = valueAtKey(cellDictionary,'type')
            if osSpaceTypeName:
                sp_ = osModel.getSpaceTypeByName(osSpaceTypeName)
                if sp_.is_initialized():
                    osSpace.setSpaceType(sp_.get())
        osBuildingStory = osBuildingStorys[0]
        for x in osBuildingStorys:
            osBuildingStoryZ = x.nominalZCoordinate().get()
            if osBuildingStoryZ + x.nominalFloortoFloorHeight().get() < osSpaceZ:
                continue
            if osBuildingStoryZ < osSpaceZ:
                osBuildingStory = x
            break
        osSpaceName = valueAtKey(cellDictionary,'name')
        if osSpaceName:
            osSpace.setName(osSpaceName)
        else:
            osSpace.setName(osBuildingStory.name().get() + "_SPACE_" + str(spaceNumber))
        osSpace.setBuildingStory(osBuildingStory)

        for faceNumber, buildingFace in enumerate(getSubTopologies(buildingCell, topologic.Face)):
            osFacePoints = []
            for vertex in getSubTopologies(buildingFace.ExternalBoundary(), topologic.Vertex):
                osFacePoints.append(openstudio.Point3d(vertex.X(), vertex.Y(), vertex.Z()))
            osSurface = openstudio.model.Surface(osFacePoints, osModel)
            faceNormal = topologic.FaceUtility.NormalAtParameters(buildingFace, 0.5, 0.5)
            osFaceNormal = openstudio.Vector3d(faceNormal.X(), faceNormal.Y(), faceNormal.Z())
            osFaceNormal.normalize()
            if osFaceNormal.dot(osSurface.outwardNormal()) < 1e-6:
                osSurface.setVertices(list(reversed(osFacePoints)))
            if math.degrees(math.acos(osSurface.outwardNormal().dot(openstudio.Vector3d(0, 0, 1)))) > 175:
                osSurface.setSurfaceType("Floor")

            osSurface.setSpace(osSpace)
            osSurface.setName(osSpace.name().get() + "_SURFACE_" + str(faceNumber))
            faceCells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
            _ = topologic.FaceUtility.AdjacentCells(buildingFace, building, faceCells)
            if len(faceCells) == 1:
                if max(list(map(lambda vertex: vertex.Z(), getSubTopologies(buildingFace, topologic.Vertex)))) < 1e-6:
                    osSurface.setOutsideBoundaryCondition("Ground")
                else:
                    if glazingRatio > 0: #user wants to use default glazing ratio on all surfaces
                        osSurface.setWindowToWallRatio(glazingRatio)
                    else: # See if there is a glazingRatio in the dictionary of the face
                        faceDictionary = buildingFace.GetDictionary()
                        if faceDictionary:
                            faceGlazingRatio = valueAtKey(faceDictionary,'glazing ratio')
                            if faceGlazingRatio and faceGlazingRatio >= 0:
                                osSurface.setWindowToWallRatio(faceGlazingRatio)
                            else: # Look for apertures and use as subsurfaces
                                apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
                                _ = buildingFace.Apertures(apertures)
                                apertures = list(apertures)
                                if len(apertures) > 0:
                                    for aperture in apertures:
                                        osSubSurfacePoints = []
                                        apertureFace = getSubTopologies(aperture.Topology(), topologic.Face)[0]
                                        for vertex in getSubTopologies(apertureFace.ExternalBoundary(), topologic.Vertex):
                                            osSubSurfacePoints.append(openstudio.Point3d(vertex.X(), vertex.Y(), vertex.Z()))
                                        osSubSurface = openstudio.model.SubSurface(osSubSurfacePoints, osModel)
                                        apertureFaceNormal = topologic.FaceUtility.NormalAtParameters(apertureFace, 0.5, 0.5)
                                        osSubSurfaceNormal = openstudio.Vector3d(apertureFaceNormal.X(), apertureFaceNormal.Y(), apertureFaceNormal.Z())
                                        osSubSurfaceNormal.normalize()
                                        if osSubSurfaceNormal.dot(osSubSurface.outwardNormal()) < 1e-6:
                                            osSubSurface.setVertices(list(reversed(osSubSurfacePoints)))
                                        osSubSurface.setSubSurfaceType("FixedWindow");
                                        osSubSurface.setSurface(osSurface)

        osThermalZone = openstudio.model.ThermalZone(osModel)
        osThermalZone.setName(osSpace.name().get() + "_THERMAL_ZONE")
        osThermalZone.setUseIdealAirLoads(True)
        osThermalZone.setVolume(topologic.CellUtility.Volume(buildingCell))
        osThermalZone.setThermostatSetpointDualSetpoint(osThermostat)
        osSpace.setThermalZone(osThermalZone)

        for x in osSpaces:
            if osSpace.boundingBox().intersects(x.boundingBox()):
                osSpace.matchSurfaces(x)
        osSpaces.append(osSpace)

    osShadingGroup = openstudio.model.ShadingSurfaceGroup(osModel)
    for faceIndex, contextFace in enumerate(getSubTopologies(shadingSurfaces, topologic.Face)):
        facePoints = []
        for aVertex in getSubTopologies(contextFace.ExternalBoundary(), topologic.Vertex):
            facePoints.append(openstudio.Point3d(aVertex.X(), aVertex.Y(), aVertex.Z()))
        aShadingSurface = openstudio.model.ShadingSurface(facePoints, osModel)
        faceNormal = topologic.FaceUtility.NormalAtParameters(contextFace, 0.5, 0.5)
        osFaceNormal = openstudio.Vector3d(faceNormal.X(), faceNormal.Y(), faceNormal.Z())
        osFaceNormal.normalize()
        if osFaceNormal.dot(aShadingSurface.outwardNormal()) < 0:
            aShadingSurface.setVertices(list(reversed(facePoints)))
        aShadingSurface.setName("SHADINGSURFACE_" + str(faceIndex))
        aShadingSurface.setShadingSurfaceGroup(osShadingGroup)

    osModel.purgeUnusedResourceObjects()
    #osModel.save(openstudio.toPath("C:/Users/wassi/osmFiles/Hola.osm"), True)
    return osModel

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvEnergyModelByTopology(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Topologic
    Tooltip: Returns an Energy Model based on the input Topology and parameters
    """
    bl_idname = 'SvEnergyModelByTopology'
    bl_label = 'EnergyModel.ByTopology'
    NorthAxis: FloatProperty(name='North Axis', default=0, min=0, max=359.99, precision=2, update=updateNode)
    GlazingRatio: FloatProperty(name='Glazing Ratio', default=0.25, min=0, max=1.0, precision=2, update=updateNode)
    CoolingTemp: FloatProperty(name='Cooling Temperature', default=25, precision=2, update=updateNode)
    HeatingTemp: FloatProperty(name='Heating Temperature', default=20, precision=2, update=updateNode)
    Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Template Energy Model')
        self.inputs.new('SvStringsSocket', 'Weather File Path')
        self.inputs.new('SvStringsSocket', 'Design Day File Path')
        self.inputs.new('SvStringsSocket', 'Building Topology')
        self.inputs.new('SvStringsSocket', 'Shading Surfaces Cluster')
        self.inputs.new('SvStringsSocket', 'Floor Levels')
        self.inputs.new('SvStringsSocket', 'Building Name')
        self.inputs.new('SvStringsSocket', 'Building Type')
        self.inputs.new('SvStringsSocket', 'Default Space Type')
        self.inputs.new('SvStringsSocket', 'North Axis').prop_name='NorthAxis'
        self.inputs.new('SvStringsSocket', 'Default Glazing Ratio').prop_name='GlazingRatio'
        self.inputs.new('SvStringsSocket', 'Cooling Temperature').prop_name='CoolingTemp'
        self.inputs.new('SvStringsSocket', 'Heating Temperature').prop_name='HeatingTemp'
        self.outputs.new('SvStringsSocket', 'Energy Model')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Replication",text="")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        modelList = self.inputs['Template Energy Model'].sv_get(deepcopy=True)
        weatherFileList = self.inputs['Weather File Path'].sv_get(deepcopy=True)
        ddyFileList = self.inputs['Design Day File Path'].sv_get(deepcopy=True)
        topologyList = self.inputs['Building Topology'].sv_get(deepcopy=True)
        shadingList = self.inputs['Shading Surfaces Cluster'].sv_get(deepcopy=True)
        floorLevelsList = self.inputs['Floor Levels'].sv_get(deepcopy=True)
        buildingNameList = self.inputs['Building Name'].sv_get(deepcopy=True)
        buildingTypeList = self.inputs['Building Type'].sv_get(deepcopy=True)
        defaultSpaceList = self.inputs['Default Space Type'].sv_get(deepcopy=True)
        northAxisList = self.inputs['North Axis'].sv_get(deepcopy=True)
        glazingRatioList = self.inputs['Default Glazing Ratio'].sv_get(deepcopy=True)
        coolingTempList = self.inputs['Cooling Temperature'].sv_get(deepcopy=True)
        heatingTempList = self.inputs['Heating Temperature'].sv_get(deepcopy=True)


        modelList = flatten(modelList)
        weatherFileList = self.inputs['Weather File Path'].sv_get(deepcopy=True)
        ddyFileList = self.inputs['Design Day File Path'].sv_get(deepcopy=True)
        topologyList = flatten(topologyList)
        shadingList = flatten(shadingList)
        #floorLevelsList does not need flattening
        buildingNameList = flatten(buildingNameList)
        buildingTypeList = flatten(buildingTypeList)
        defaultSpaceList = flatten(defaultSpaceList)
        northAxisList = flatten(northAxisList)
        glazingRatioList = flatten(glazingRatioList)
        coolingTempList = flatten(coolingTempList)
        heatingTempList = flatten(heatingTempList)
        inputs = [modelList, weatherFileList, ddyFileList, topologyList, shadingList, floorLevelsList, buildingNameList, buildingTypeList, defaultSpaceList, northAxisList, glazingRatioList, coolingTempList, heatingTempList]
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
        self.outputs['Energy Model'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvEnergyModelByTopology)

def unregister():
    bpy.utils.unregister_class(SvEnergyModelByTopology)
