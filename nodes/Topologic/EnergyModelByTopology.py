# Based on code kindly provided by Adrià González Esteve
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication
from . import DictionaryValueAtKey
from . import TopologySubTopologies

try:
	import openstudio
except:
	raise Exception("Error: Could not import openstudio.")
import math

def getKeyName(d, keyName):
    keys = d.Keys()
    for key in keys:
        if key.lower() == keyName.lower():
            return key
    return None

def createUniqueName(name, nameList, number):
    if not (name in nameList):
        return name
    elif not ((name+"_"+str(number)) in nameList):
        return name+"_"+str(number)
    else:
        return createUniqueName(name,nameList, number+1)

def processItem(item):
    osModelPath = item[0]
    weatherFilePath = item[1]
    designDayFilePath = item[2]
    buildingTopology = item[3]
    shadingSurfaces = item[4]
    floorLevels = item[5]
    buildingName = item[6]
    buildingType = item[7]
    defaultSpaceType = item[8]
    northAxis = item[9]
    glazingRatio = item[10]
    coolingTemp = item[11]
    heatingTemp = item[12]
    roomNameKey = item[13]
    roomTypeKey = item[14]
    translator = openstudio.osversion.VersionTranslator()
    osmFile = openstudio.openstudioutilitiescore.toPath(osModelPath)
    osModel = translator.loadModel(osmFile)
    if osModel.isNull():
        raise Exception("File Path is not a valid path to an OpenStudio Model")
        return None
    else:
        osModel = osModel.get()
    osEPWFile = openstudio.openstudioutilitiesfiletypes.EpwFile.load(openstudio.toPath(weatherFilePath))
    if osEPWFile.is_initialized():
        osEPWFile = osEPWFile.get()
        openstudio.model.WeatherFile.setWeatherFile(osModel, osEPWFile)
    ddyModel = openstudio.openstudioenergyplus.loadAndTranslateIdf(openstudio.toPath(designDayFilePath))
    if ddyModel.is_initialized():
        ddyModel = ddyModel.get()
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
    spaceNames = []
    for spaceNumber, buildingCell in enumerate(TopologySubTopologies.processItem([buildingTopology, "Cell"])):
        osSpace = openstudio.model.Space(osModel)
        osSpaceZ = buildingCell.CenterOfMass().Z()
        osBuildingStory = osBuildingStorys[0]
        for x in osBuildingStorys:
            osBuildingStoryZ = x.nominalZCoordinate().get()
            if osBuildingStoryZ + x.nominalFloortoFloorHeight().get() < osSpaceZ:
                continue
            if osBuildingStoryZ < osSpaceZ:
                osBuildingStory = x
            break
        osSpace.setBuildingStory(osBuildingStory)
        cellDictionary = buildingCell.GetDictionary()
        if cellDictionary:
            if roomTypeKey:
                keyType = getKeyName(cellDictionary, roomTypeKey)
            else:
                keyType = getKeyName(cellDictionary, 'type')
            osSpaceTypeName = DictionaryValueAtKey.processItem([cellDictionary,keyType])
            if osSpaceTypeName:
                sp_ = osModel.getSpaceTypeByName(osSpaceTypeName)
                if sp_.is_initialized():
                    osSpace.setSpaceType(sp_.get())
            if roomNameKey:
                keyName = getKeyName(cellDictionary, roomNameKey)

            else:
                keyName = getKeyName(cellDictionary, 'name')
            osSpaceName = None
            if keyName:
                osSpaceName = createUniqueName(DictionaryValueAtKey.processItem([cellDictionary,keyName]),spaceNames, 1)
            if osSpaceName:
                osSpace.setName(osSpaceName)
        else:
            osSpaceName = osBuildingStory.name().get() + "_SPACE_" + str(spaceNumber)
            osSpace.setName(osSpaceName)
            sp_ = osModel.getSpaceTypeByName(defaultSpaceType)
            if sp_.is_initialized():
                osSpace.setSpaceType(sp_.get())
        spaceNames.append(osSpaceName)
        cellFaces = TopologySubTopologies.processItem([buildingCell, "Face"])
        if cellFaces:
            for faceNumber, buildingFace in enumerate(cellFaces):
                osFacePoints = []
                for vertex in TopologySubTopologies.processItem([buildingFace.ExternalBoundary(), "Vertex"]):
                    osFacePoints.append(openstudio.Point3d(vertex.X(), vertex.Y(), vertex.Z()))
                osSurface = openstudio.model.Surface(osFacePoints, osModel)
                faceNormal = topologic.FaceUtility.NormalAtParameters(buildingFace, 0.5, 0.5)
                osFaceNormal = openstudio.Vector3d(faceNormal[0], faceNormal[1], faceNormal[2])
                osFaceNormal.normalize()
                if osFaceNormal.dot(osSurface.outwardNormal()) < 1e-6:
                    osSurface.setVertices(list(reversed(osFacePoints)))
                osSurface.setSpace(osSpace)
                faceCells = []
                _ = topologic.FaceUtility.AdjacentCells(buildingFace, buildingTopology, faceCells)
                if len(faceCells) == 1: #Exterior Surfaces
                    osSurface.setOutsideBoundaryCondition("Outdoors")
                    if (math.degrees(math.acos(osSurface.outwardNormal().dot(openstudio.Vector3d(0, 0, 1)))) > 135) or (math.degrees(math.acos(osSurface.outwardNormal().dot(openstudio.Vector3d(0, 0, 1)))) < 45):
                        osSurface.setSurfaceType("RoofCeiling")
                        osSurface.setOutsideBoundaryCondition("Outdoors")
                        osSurface.setName(osSpace.name().get() + "_TopHorizontalSlab_" + str(faceNumber))
                        if max(list(map(lambda vertex: vertex.Z(), TopologySubTopologies.processItem([buildingFace, "Vertex"])))) < 1e-6:
                            osSurface.setSurfaceType("Floor")
                            osSurface.setOutsideBoundaryCondition("Ground")
                            osSurface.setName(osSpace.name().get() + "_BottomHorizontalSlab_" + str(faceNumber))
                    else:
                        osSurface.setSurfaceType("Wall")
                        osSurface.setOutsideBoundaryCondition("Outdoors")
                        osSurface.setName(osSpace.name().get() + "_ExternalVerticalFace_" + str(faceNumber))
                        # Check for exterior apertures
                        faceDictionary = buildingFace.GetDictionary()
                        apertures = []
                        _ = buildingFace.Apertures(apertures)
                        if len(apertures) > 0:
                            for aperture in apertures:
                                osSubSurfacePoints = []
                                #apertureFace = TopologySubTopologies.processItem([aperture, topologic.Face])[0]
                                apertureFace = topologic.Aperture.Topology(aperture)
                                for vertex in TopologySubTopologies.processItem([apertureFace.ExternalBoundary(), "Vertex"]):
                                    osSubSurfacePoints.append(openstudio.Point3d(vertex.X(), vertex.Y(), vertex.Z()))
                                osSubSurface = openstudio.model.SubSurface(osSubSurfacePoints, osModel)
                                apertureFaceNormal = topologic.FaceUtility.NormalAtParameters(apertureFace, 0.5, 0.5)
                                osSubSurfaceNormal = openstudio.Vector3d(apertureFaceNormal[0], apertureFaceNormal[1], apertureFaceNormal[2])
                                osSubSurfaceNormal.normalize()
                                if osSubSurfaceNormal.dot(osSubSurface.outwardNormal()) < 1e-6:
                                    osSubSurface.setVertices(list(reversed(osSubSurfacePoints)))
                                osSubSurface.setSubSurfaceType("FixedWindow")
                                osSubSurface.setSurface(osSurface)
                        else:
                                # Get the dictionary keys
                                keys = faceDictionary.Keys()
                                if ('TOPOLOGIC_glazing_ratio' in keys):
                                    faceGlazingRatio = DictionaryValueAtKey.processItem([faceDictionary,'TOPOLOGIC_glazing_ratio'])
                                    if faceGlazingRatio and faceGlazingRatio >= 0.01:
                                        osSurface.setWindowToWallRatio(faceGlazingRatio)
                                else:
                                    if glazingRatio > 0.01: #Glazing ratio must be more than 1% to make any sense.
                                        osSurface.setWindowToWallRatio(glazingRatio)
                else: #Interior Surfaces
                    if (math.degrees(math.acos(osSurface.outwardNormal().dot(openstudio.Vector3d(0, 0, 1)))) > 135):
                        osSurface.setSurfaceType("Floor")
                        osSurface.setName(osSpace.name().get() + "_InternalHorizontalFace_" + str(faceNumber))
                    elif (math.degrees(math.acos(osSurface.outwardNormal().dot(openstudio.Vector3d(0, 0, 1)))) < 40):
                        osSurface.setSurfaceType("RoofCeiling")
                        osSurface.setName(osSpace.name().get() + "_InternalHorizontalFace_" + str(faceNumber))
                    else:
                        osSurface.setSurfaceType("Wall")
                        osSurface.setName(osSpace.name().get() + "_InternalVerticalFace_" + str(faceNumber))
                    # Check for interior apertures
                    faceDictionary = buildingFace.GetDictionary()
                    apertures = []
                    _ = buildingFace.Apertures(apertures)
                    if len(apertures) > 0:
                        for aperture in apertures:
                            osSubSurfacePoints = []
                            #apertureFace = TopologySubTopologies.processItem([aperture, "Face"])[0]
                            apertureFace = topologic.Aperture.Topology(aperture)
                            for vertex in TopologySubTopologies.processItem([apertureFace.ExternalBoundary(), "Vertex"]):
                                osSubSurfacePoints.append(openstudio.Point3d(vertex.X(), vertex.Y(), vertex.Z()))
                            osSubSurface = openstudio.model.SubSurface(osSubSurfacePoints, osModel)
                            apertureFaceNormal = topologic.FaceUtility.NormalAtParameters(apertureFace, 0.5, 0.5)
                            osSubSurfaceNormal = openstudio.Vector3d(apertureFaceNormal[0], apertureFaceNormal[1], apertureFaceNormal[2])
                            osSubSurfaceNormal.normalize()
                            if osSubSurfaceNormal.dot(osSubSurface.outwardNormal()) < 1e-6:
                                osSubSurface.setVertices(list(reversed(osSubSurfacePoints)))
                            osSubSurface.setSubSurfaceType("Door") #We are assuming all interior apertures to be doors
                            osSubSurface.setSurface(osSurface)

        osThermalZone = openstudio.model.ThermalZone(osModel)
        osThermalZone.setVolume(topologic.CellUtility.Volume(buildingCell))
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
    if not isinstance(shadingSurfaces,int):
        for faceIndex, shadingFace in enumerate(TopologySubTopologies.processItem([shadingSurfaces, "Face"])):
            facePoints = []
            for aVertex in TopologySubTopologies.processItem([shadingFace.ExternalBoundary(), "Vertex"]):
                facePoints.append(openstudio.Point3d(aVertex.X(), aVertex.Y(), aVertex.Z()))
            aShadingSurface = openstudio.model.ShadingSurface(facePoints, osModel)
            faceNormal = topologic.FaceUtility.NormalAtParameters(shadingFace, 0.5, 0.5)
            osFaceNormal = openstudio.Vector3d(faceNormal[0], faceNormal[1], faceNormal[2])
            osFaceNormal.normalize()
            if osFaceNormal.dot(aShadingSurface.outwardNormal()) < 0:
                aShadingSurface.setVertices(list(reversed(facePoints)))
            aShadingSurface.setName("SHADINGSURFACE_" + str(faceIndex))
            aShadingSurface.setShadingSurfaceGroup(osShadingGroup)

    osModel.purgeUnusedResourceObjects()
    return osModel

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvEnergyModelByTopology(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Topologic
    Tooltip: Returns an Energy Model based on the input Topology and parameters
    """
    bl_idname = 'SvEnergyModelByTopology'
    bl_label = 'EnergyModel.ByTopology'
    OSMFilePath: StringProperty(name="Template (OSM) File Path", default="", subtype="FILE_PATH")
    EPWFilePath: StringProperty(name="Weather (EPW) File Path", default="", subtype="FILE_PATH")
    DDYFilePath: StringProperty(name="Design Day (DDY) File Path", default="", subtype="FILE_PATH")
    NorthAxis: FloatProperty(name='North Axis', default=0, min=0, max=359.99, precision=2, update=updateNode)
    BuildingName: StringProperty(name='Building Name', default="TopologicBuilding", update=updateNode)
    BuildingType: StringProperty(name='Building Type', default="Commercial", update=updateNode)
    DefaultSpaceType: StringProperty(name='Default Space Type', default="189.1-2009 - Office - WholeBuilding - Lg Office - CZ4-8", update=updateNode)
    GlazingRatio: FloatProperty(name='Glazing Ratio', default=0.25, min=0, max=1.0, precision=2, update=updateNode)
    CoolingTemp: FloatProperty(name='Cooling Temperature', default=25, precision=2, update=updateNode)
    HeatingTemp: FloatProperty(name='Heating Temperature', default=20, precision=2, update=updateNode)
    RoomNameKey: StringProperty(name='Room Name Key', default="Name", update=updateNode)
    RoomTypeKey: StringProperty(name='Room Type Key', default="Type", update=updateNode)

    Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Template (OSM) File Path').prop_name='OSMFilePath'
        self.inputs.new('SvStringsSocket', 'Weather (EPW) File Path').prop_name='EPWFilePath'
        self.inputs.new('SvStringsSocket', 'Design Day (DDY) File Path').prop_name='DDYFilePath'
        self.inputs.new('SvStringsSocket', 'Building Topology')
        self.inputs.new('SvStringsSocket', 'Shading Surfaces Cluster')
        self.inputs.new('SvStringsSocket', 'Floor Z Levels')
        self.inputs.new('SvStringsSocket', 'Building Name').prop_name='BuildingName'
        self.inputs.new('SvStringsSocket', 'Building Type').prop_name='BuildingType'
        self.inputs.new('SvStringsSocket', 'Default Space Type').prop_name='DefaultSpaceType'
        self.inputs.new('SvStringsSocket', 'North Axis').prop_name='NorthAxis'
        self.inputs.new('SvStringsSocket', 'Default Glazing Ratio').prop_name='GlazingRatio'
        self.inputs.new('SvStringsSocket', 'Cooling Temperature').prop_name='CoolingTemp'
        self.inputs.new('SvStringsSocket', 'Heating Temperature').prop_name='HeatingTemp'
        self.inputs.new('SvStringsSocket', 'Room Name Key').prop_name='RoomNameKey'
        self.inputs.new('SvStringsSocket', 'Room Type Key').prop_name='RoomTypeKey'
        self.outputs.new('SvStringsSocket', 'Energy Model')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Replication",text="")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        modelList = self.inputs['Template (OSM) File Path'].sv_get(deepcopy=True)
        weatherFileList = self.inputs['Weather (EPW) File Path'].sv_get(deepcopy=True)
        ddyFileList = self.inputs['Design Day (DDY) File Path'].sv_get(deepcopy=True)
        buildingTopologyList = self.inputs['Building Topology'].sv_get(deepcopy=True)
        if (self.inputs['Shading Surfaces Cluster'].is_linked):
            shadingList = self.inputs['Shading Surfaces Cluster'].sv_get(deepcopy=True)
        else:
            shadingList = [0]
        floorLevelsList = self.inputs['Floor Z Levels'].sv_get(deepcopy=True)
        buildingNameList = self.inputs['Building Name'].sv_get(deepcopy=True)
        buildingTypeList = self.inputs['Building Type'].sv_get(deepcopy=True)
        defaultSpaceList = self.inputs['Default Space Type'].sv_get(deepcopy=True)
        northAxisList = self.inputs['North Axis'].sv_get(deepcopy=True)
        glazingRatioList = self.inputs['Default Glazing Ratio'].sv_get(deepcopy=True)
        coolingTempList = self.inputs['Cooling Temperature'].sv_get(deepcopy=True)
        heatingTempList = self.inputs['Heating Temperature'].sv_get(deepcopy=True)
        roomNameKeyList = self.inputs['Room Name Key'].sv_get(deepcopy=True)
        roomTypeKeyList = self.inputs['Room Type Key'].sv_get(deepcopy=True)



        modelList = Replication.flatten(modelList)
        weatherFileList = Replication.flatten(weatherFileList)
        ddyFileList = Replication.flatten(ddyFileList)
        buildingTopologyList = Replication.flatten(buildingTopologyList)
        shadingList = Replication.flatten(shadingList)
        #floorLevelsList does not need flattening
        buildingNameList = Replication.flatten(buildingNameList)
        buildingTypeList = Replication.flatten(buildingTypeList)
        defaultSpaceList = Replication.flatten(defaultSpaceList)
        northAxisList = Replication.flatten(northAxisList)
        glazingRatioList = Replication.flatten(glazingRatioList)
        coolingTempList = Replication.flatten(coolingTempList)
        heatingTempList = Replication.flatten(heatingTempList)
        roomNameKeyList = Replication.flatten(roomNameKeyList)
        roomTypeKeyList = Replication.flatten(roomTypeKeyList)
        inputs = [modelList, weatherFileList, ddyFileList, buildingTopologyList, shadingList, floorLevelsList, buildingNameList, buildingTypeList, defaultSpaceList, northAxisList, glazingRatioList, coolingTempList, heatingTempList, roomNameKeyList, roomTypeKeyList]
        if ((self.Replication) == "Default"):
            inputs = Replication.iterate(inputs)
            inputs = Replication.transposeList(inputs)
        if ((self.Replication) == "Trim"):
            inputs = Replication.trim(inputs)
            inputs = Replication.transposeList(inputs)
        elif ((self.Replication) == "Iterate"):
            inputs = Replication.iterate(inputs)
            inputs = Replication.transposeList(inputs)
        elif ((self.Replication) == "Repeat"):
            inputs = Replication.repeat(inputs)
            inputs = Replication.transposeList(inputs)
        elif ((self.Replication) == "Interlace"):
            inputs = list(Replication.interlace(inputs))
        outputs = []
        for anInput in inputs:
            outputs.append(processItem(anInput))
        self.outputs['Energy Model'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvEnergyModelByTopology)

def unregister():
    bpy.utils.unregister_class(SvEnergyModelByTopology)
