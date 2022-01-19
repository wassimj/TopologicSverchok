# Based on code kindly provided by Adrià González Esteve
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time

from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face
from honeybee.shade import Shade
from honeybee.aperture import Aperture
from honeybee.door import Door
from honeybee.boundarycondition import boundary_conditions
import honeybee.facetype
from honeybee.facetype import face_types, Floor, RoofCeiling

from honeybee_energy.constructionset import ConstructionSet
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.shade import ShadeConstruction
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.load.setpoint import Setpoint
from honeybee_energy.load.hotwater import  ServiceHotWater
from honeybee_energy.ventcool.opening import VentilationOpening
from honeybee_energy.ventcool.control import VentilationControl
from honeybee_energy.ventcool import afn
from honeybee_energy.ventcool.simulation import VentilationSimulationControl
from honeybee_energy.hvac.allair.vav import VAV
from honeybee_energy.hvac.doas.fcu import FCUwithDOAS
from honeybee_energy.hvac.heatcool.windowac import WindowAC

import honeybee_energy.lib.programtypes as prog_type_lib
import honeybee_energy.lib.constructionsets as constr_set_lib

import honeybee_energy.lib.scheduletypelimits as schedule_types
from honeybee_energy.lib.materials import clear_glass, air_gap, roof_membrane, \
    wood, insulation
from honeybee_energy.lib.constructions import generic_exterior_wall, \
    generic_interior_wall, generic_interior_floor, generic_interior_ceiling, \
    generic_double_pane

from honeybee_radiance.modifierset import ModifierSet
from honeybee_radiance.modifier.material import Glass, Plastic, Trans
from honeybee_radiance.dynamic import RadianceShadeState, RadianceSubFaceState, \
    StateGeometry

from ladybug.dt import Time
from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.polyface import Polyface3D

import os
import json
import random

try:
	import openstudio
except:
	raise Exception("Error: Could not import openstudio.")
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

def getSubTopologies(topology, subTopologyClass):
    subTopologies = []
    if subTopologyClass == topologic.Vertex:
        _ = topology.Vertices(None, subTopologies)
    elif subTopologyClass == topologic.Edge:
        _ = topology.Edges(None, subTopologies)
    elif subTopologyClass == topologic.Wire:
        _ = topology.Wires(None, subTopologies)
    elif subTopologyClass == topologic.Face:
        _ = topology.Faces(None, subTopologies)
    elif subTopologyClass == topologic.Shell:
        _ = topology.Shells(None, subTopologies)
    elif subTopologyClass == topologic.Cell:
        _ = topology.Cells(None, subTopologies)
    elif subTopologyClass == topologic.CellComplex:
        _ = topology.CellComplexes(None, subTopologies)
    return subTopologies

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

def valueAtKey(item, key):
    if key == None:
        return None
    try:
        attr = item.ValueAtKey(key)
    except:
        return None
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

def cellFloor(cell):
    faces = []
    _ = cell.Faces(None, faces)
    c = [x.CenterOfMass().Z() for x in faces]
    return round(min(c),2)

def floorLevels(cells, min_difference):
    floors = [cellFloor(x) for x in cells]
    floors = list(set(floors)) #create a unique list
    floors.sort()
    returnList = []
    for aCell in cells:
        for floorNumber, aFloor in enumerate(floors):
            if abs(cellFloor(aCell) - aFloor) > min_difference:
                continue
            returnList.append("Floor"+str(floorNumber).zfill(2))
            break
    return returnList

def getKeyName(d, keyName):
    keys = d.Keys()
    for key in keys:
        if key.lower() == keyName.lower():
            return key
    return None

def processItem(item):
    tpBuilding = item[0]
    tpShadingFacesCluster = item[1]
    buildingName = item[2]
    defaultProgramIdentifier = item[3]
    defaultConstructionSetIdentifier = item[4]
    coolingSetpoint = item[5]
    heatingSetpoint = item[6]
    humidifyingSetpoint = item[7]
    dehumidifyingSetpoint = item[8]
    if buildingName:
        buildingName = buildingName.replace(" ","_")
    else:
        buildingName = "GENERICBUILDING"
    rooms = []
    tpCells = []
    _ = tpBuilding.Cells(None, tpCells)
    # Sort cells by Z Levels
    tpCells.sort(key=lambda c: cellFloor(c), reverse=False)
    fl = floorLevels(tpCells, 2)
    for spaceNumber, tpCell in enumerate(tpCells):
        tpDictionary = tpCell.GetDictionary()
        tpCellName = None
        tpCellStory = None
        tpCellProgramIdentifier = None
        tpCellConstructionSetIdentifier = None
        tpCellConditioned = True
        if tpDictionary:
            keyName = getKeyName(tpDictionary, 'Name')
            tpCellName = valueAtKey(tpDictionary,keyName)
            if tpCellName:
                tpCellName = tpCellName.replace(" ","_")+(str(spaceNumber+1))
            else:
                tpCellName = "GENERICROOM_"+(str(spaceNumber+1))
            keyName = getKeyName(tpDictionary, 'Story')
            tpCellStory = valueAtKey(tpDictionary, keyName)
            if tpCellStory:
                tpCellStory = tpCellStory.replace(" ","_")
            else:
                tpCellStory = fl[spaceNumber]
            keyName = getKeyName(tpDictionary, 'Program')
            tpCellProgramIdentifier = valueAtKey(tpDictionary, keyName)
            if tpCellProgramIdentifier:
                program = prog_type_lib.program_type_by_identifier(tpCellProgramIdentifier)
            elif defaultProgramIdentifier:
                program = prog_type_lib.program_type_by_identifier(defaultProgramIdentifier)
            else:
                program = prog_type_lib.office_program #Default Office Program as a last resort
            keyName = getKeyName(tpDictionary, 'construction_set')
            tpCellConstructionSetIdentifier = valueAtKey(tpDictionary, keyName)
            if tpCellConstructionSetIdentifier:
                constr_set = constr_set_lib.construction_set_by_identifier(tpCellConstructionSetIdentifier)
            elif defaultConstructionSetIdentifier:
                constr_set = constr_set_lib.construction_set_by_identifier(defaultConstructionSetIdentifier)
            else:
                constr_set = constr_set_lib.construction_set_by_identifier("Default Generic Construction Set")
        tpCellFaces = []
        _ = tpCell.Faces(None, tpCellFaces)
        if tpCellFaces:
            hbRoomFaces = []
            for tpFaceNumber, tpCellFace in enumerate(tpCellFaces):
                tpCellFaceNormal = topologic.FaceUtility.NormalAtParameters(tpCellFace, 0.5, 0.5)
                hbRoomFacePoints = []
                tpFaceVertices = []
                _ = tpCellFace.ExternalBoundary().Vertices(None, tpFaceVertices)
                for tpVertex in tpFaceVertices:
                    hbRoomFacePoints.append(Point3D(tpVertex.X(), tpVertex.Y(), tpVertex.Z()))
                hbRoomFace = Face(tpCellName+'_Face_'+str(tpFaceNumber+1), Face3D(hbRoomFacePoints))
                tpFaceApertures = []
                _ = tpCellFace.Apertures(tpFaceApertures)
                if tpFaceApertures:
                    for tpFaceApertureNumber, tpFaceAperture in enumerate(tpFaceApertures):
                        apertureTopology = topologic.Aperture.Topology(tpFaceAperture)
                        tpFaceApertureDictionary = apertureTopology.GetDictionary()
                        if tpFaceApertureDictionary:
                            tpFaceApertureType = valueAtKey(tpFaceApertureDictionary,'type')
                        hbFaceAperturePoints = []
                        tpFaceApertureVertices = []
                        _ = apertureTopology.ExternalBoundary().Vertices(None, tpFaceApertureVertices)
                        for tpFaceApertureVertex in tpFaceApertureVertices:
                            hbFaceAperturePoints.append(Point3D(tpFaceApertureVertex.X(), tpFaceApertureVertex.Y(), tpFaceApertureVertex.Z()))
                        if(tpFaceApertureType):
                            if ("door" in tpFaceApertureType.lower()):
                                hbFaceAperture = Door(tpCellName+'_Face_'+str(tpFaceNumber+1)+'_Door_'+str(tpFaceApertureNumber), Face3D(hbFaceAperturePoints))
                            else:
                                hbFaceAperture = Aperture(tpCellName+'_Face_'+str(tpFaceNumber+1)+'_Window_'+str(tpFaceApertureNumber), Face3D(hbFaceAperturePoints))
                        else:
                            hbFaceAperture = Aperture(tpCellName+'_Face_'+str(tpFaceNumber+1)+'_Window_'+str(tpFaceApertureNumber), Face3D(hbFaceAperturePoints))
                        hbRoomFace.add_aperture(hbFaceAperture)
                else:
                    tpFaceDictionary = tpCellFace.GetDictionary()
                    if (abs(tpCellFaceNormal[2]) < 1e-6) and tpFaceDictionary: #It is a mostly vertical wall and has a dictionary
                        apertureRatio = valueAtKey(tpFaceDictionary,'apertureRatio')
                        if apertureRatio:
                            hbRoomFace.apertures_by_ratio(apertureRatio, tolerance=0.01)
                fType = honeybee.facetype.get_type_from_normal(Vector3D(tpCellFaceNormal[0],tpCellFaceNormal[1],tpCellFaceNormal[2]), roof_angle=30, floor_angle=150)
                hbRoomFace.type = fType
                hbRoomFaces.append(hbRoomFace)
            room = Room(tpCellName, hbRoomFaces, 0.01, 1)
            heat_setpt = ScheduleRuleset.from_constant_value('Room Heating', heatingSetpoint, schedule_types.temperature)
            cool_setpt = ScheduleRuleset.from_constant_value('Room Cooling', coolingSetpoint, schedule_types.temperature)
            humidify_setpt = ScheduleRuleset.from_constant_value('Room Humidifying', humidifyingSetpoint, schedule_types.humidity)
            dehumidify_setpt = ScheduleRuleset.from_constant_value('Room Dehumidifying', dehumidifyingSetpoint, schedule_types.humidity)
            setpoint = Setpoint('Room Setpoint', heat_setpt, cool_setpt, humidify_setpt, dehumidify_setpt)
            simple_office = ScheduleDay('Simple Weekday', [0, 1, 0], [Time(0, 0), Time(9, 0), Time(17, 0)]) #Todo: Remove hardwired scheduleday
            schedule = ScheduleRuleset('Office Water Use', simple_office, None, schedule_types.fractional) #Todo: Remove hardwired schedule
            shw = ServiceHotWater('Office Hot Water', 0.1, schedule) #Todo: Remove hardwired schedule hot water
            room.properties.energy.program_type = program
            room.properties.energy.construction_set = constr_set
            room.properties.energy.add_default_ideal_air() #Ideal Air Exchange
            room.properties.energy.setpoint = setpoint #Heating/Cooling/Humidifying/Dehumidifying
            room.properties.energy.service_hot_water = shw #Service Hot Water
            if tpCellStory:
                room.story = tpCellStory
            rooms.append(room)
    Room.solve_adjacency(rooms, 0.01)
    #for room in rooms:
        #room.properties.energy.construction_set = constr_set
    #Room.stories_by_floor_height(rooms, min_difference=2.0)

    if(tpShadingFacesCluster):
        hbShades = []
        tpShadingFaces = []
        _ = tpShadingFacesCluster.Faces(None, tpShadingFaces)
        for faceIndex, tpShadingFace in enumerate(tpShadingFaces):
            faceVertices = []
            _ = tpShadingFace.ExternalBoundary().Vertices(None, faceVertices)
            facePoints = []
            for aVertex in faceVertices:
                facePoints.append(Point3D(aVertex.X(), aVertex.Y(), aVertex.Z()))
            hbShadingFace = Face3D(facePoints, None, [])
            hbShade = Shade("SHADINGSURFACE_" + str(faceIndex+1), hbShadingFace)
            hbShades.append(hbShade)
    model = Model(buildingName, rooms, orphaned_shades=hbShades)
    return model

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvHBModelByTopology(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Topologic
    Tooltip: Returns an HBModel based on the input Topology and parameters
    """
    bl_idname = 'SvHBModelByTopology'
    bl_label = 'HBModel.ByTopology'
    CoolingSetpoint: FloatProperty(name='Cooling Setpoint', default=25, precision=2, update=updateNode)
    HeatingSetpoint: FloatProperty(name='Heating Setpoint', default=20, precision=2, update=updateNode)
    HumidifyingSetpoint: FloatProperty(name='Humidifying Setpoint', default=30, precision=2, update=updateNode)
    DehumidifyingSetpoint: FloatProperty(name='Dehumidifying Setpoint', default=55, precision=2, update=updateNode)
    BuildingName: StringProperty(name='Building Name', default="Generic_Building", update=updateNode)
    DefaultProgramIdentifier: StringProperty(name='Default Program Identifier', default="Generic Office Program", update=updateNode)
    DefaultConstructionSet: StringProperty(name='Default Construction Set', default="Default Generic Construction Set", update=updateNode)
    Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Building Topology')
        self.inputs.new('SvStringsSocket', 'Shading Faces Cluster')
        self.inputs.new('SvStringsSocket', 'Building Name').prop_name='BuildingName'
        self.inputs.new('SvStringsSocket', 'Default Program Identifier').prop_name='DefaultProgramIdentifier'
        self.inputs.new('SvStringsSocket', 'Default Construction Set Identifier').prop_name='DefaultConstructionSet'
        self.inputs.new('SvStringsSocket', 'Cooling Setpoint').prop_name='CoolingSetpoint'
        self.inputs.new('SvStringsSocket', 'Heating Setpoint').prop_name='HeatingSetpoint'
        self.inputs.new('SvStringsSocket', 'Humidifying Setpoint').prop_name='HumidifyingSetpoint'
        self.inputs.new('SvStringsSocket', 'Dehumidifying Setpoint').prop_name='DehumidifyingSetpoint'
        self.outputs.new('SvStringsSocket', 'HB Model')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Replication",text="")

    def process(self):
        start = time.time()
        if not any(socket.is_linked for socket in self.outputs):
            return
        buildingTopologyList = self.inputs['Building Topology'].sv_get(deepcopy=True)
        if (self.inputs['Shading Faces Cluster'].is_linked):
            shadingList = self.inputs['Shading Faces Cluster'].sv_get(deepcopy=True)
            shadingList = flatten(shadingList)
        else:
            shadingList = [topologic.Cluster.ByTopologies([topologic.Vertex.ByCoordinates(0,0,0)])] #Create a fake Cluster with no faces
        buildingNameList = self.inputs['Building Name'].sv_get(deepcopy=True)
        defaultProgramIdentifierList = self.inputs['Default Program Identifier'].sv_get(deepcopy=True)
        defaultConstructionSetIdentifierList = self.inputs['Default Construction Set Identifier'].sv_get(deepcopy=True)
        coolingSetpointList = self.inputs['Cooling Setpoint'].sv_get(deepcopy=True)
        heatingSetpointList = self.inputs['Heating Setpoint'].sv_get(deepcopy=True)
        humidifyingSetpointList = self.inputs['Humidifying Setpoint'].sv_get(deepcopy=True)
        dehumidifyingSetpointList = self.inputs['Dehumidifying Setpoint'].sv_get(deepcopy=True)

        buildingTopologyList = flatten(buildingTopologyList)
        buildingNameList = flatten(buildingNameList)
        defaultProgramIdentifierList = flatten(defaultProgramIdentifierList)
        defaultConstructionSetIdentifierList = flatten(defaultConstructionSetIdentifierList)
        coolingSetpointList = flatten(coolingSetpointList)
        heatingSetpointList = flatten(heatingSetpointList)
        humidifyingSetpointList = flatten(humidifyingSetpointList)
        dehumidifyingSetpointList = flatten(dehumidifyingSetpointList)

        inputs = [buildingTopologyList, shadingList, buildingNameList, defaultProgramIdentifierList, defaultConstructionSetIdentifierList, coolingSetpointList, heatingSetpointList, humidifyingSetpointList, dehumidifyingSetpointList]
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
        self.outputs['HB Model'].sv_set(outputs)
        end = time.time()
        print("HBModel.ByTopology Operation consumed "+str(round(end - start,2)*1000)+" ms")

def register():
    bpy.utils.register_class(SvHBModelByTopology)

def unregister():
    bpy.utils.unregister_class(SvHBModelByTopology)
