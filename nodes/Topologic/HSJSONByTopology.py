# Based on code kindly provided by Adrià González Esteve
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face
from honeybee.shade import Shade
from honeybee.aperture import Aperture
from honeybee.door import Door
from honeybee.boundarycondition import boundary_conditions
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
    subTopologies = []
    if subTopologyClass == topologic.Vertex:
        _ = topology.Vertices(subTopologies)
    elif subTopologyClass == topologic.Edge:
        _ = topology.Edges(subTopologies)
    elif subTopologyClass == topologic.Wire:
        _ = topology.Wires(subTopologies)
    elif subTopologyClass == topologic.Face:
        _ = topology.Faces(subTopologies)
    elif subTopologyClass == topologic.Shell:
        _ = topology.Shells(subTopologies)
    elif subTopologyClass == topologic.Cell:
        _ = topology.Cells(subTopologies)
    elif subTopologyClass == topologic.CellComplex:
        _ = topology.CellComplexes(subTopologies)
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

def processItem(item):

    osModel = item[0]
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

    rooms = []
    buildingCells = []
    _ = buildingTopology.Cells(buildingCells)
    for spaceNumber, buildingCell in enumerate(buildingCells):
        cellDictionary = buildingCell.GetDictionary()
        if cellDictionary:
            cellName = valueAtKey(cellDictionary,'name')
        cellFaces = []
        _ = buildingCell.Faces(cellFaces)
        if cellFaces:
            hbRoomFaces = []
            for faceNumber, buildingFace in enumerate(cellFaces):
                hbFacePoints = []
                faceVertices = []
                _ = buildingFace.ExternalBoundary().Vertices(faceVertices)
                for vertex in faceVertices:
                    hbFacePoints.append(Point3d(vertex.X(), vertex.Y(), vertex.Z()))
                hbFace = openstudio.model.Surface(osFacePoints, osModel)
                hbRoomFaces.append(Face('osSpaceName'+str(faceNumber), Face3D(hbFacePoints)))
            room = Room(osSpaceName, hbRoomFaces, 0.01, 1))
            room_setpoint = room.properties.energy.setpoint.duplicate()
            room_setpoint.identifier = 'Humidity Controlled Room Setpt'
            room_setpoint.cooling_setpoint = coolingTemp
            room_setpoint.heating_setpoint = heatingTemp
            room_setpoint.humidifying_setpoint = 30
            room_setpoint.dehumidifying_setpoint = 55
            room.properties.energy.setpoint = room_setpoint
            room.properties.energy.program_type = prog_type_lib.office_program
            rooms.append(room)
    Room.solve_adjacency(rooms, 0.01)


    hbShades = []
    _ = shadingSurfaces.Faces(shadingFaces)
    for faceIndex, shadingFace in enumerate(shadingFaces):
        faceVertices = []
        _ = shadingFace.ExternalBoundary().Vertices(faceVertices)
        facePoints = []
        for aVertex in faceVertices:
            facePoints.append(Point3d(aVertex.X(), aVertex.Y(), aVertex.Z()))
        faceNormal = topologic.FaceUtility.NormalAtParameters(shadingFace, 0.5, 0.5)
        osFaceNormal = openstudio.Vector3d(faceNormal[0], faceNormal[1], faceNormal[2])
        osFaceNormal.normalize()
        if osFaceNormal.dot(aShadingSurface.outwardNormal()) < 0:
            hbShadingFace = Face3D(list(reversed(facePoints), None, [])
        else:
            aShadingSurface = Face3D(list(reversed(facePoints), None, [])
        hbShade = Shade("SHADINGSURFACE_" + str(faceIndex), hbShadingFace)
        hbShades.append(hbShade)
    model = Model('TopologicModel', rooms, orphaned_shades=hbShades)
    return model.to_dict()

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvHSJSONByTopology(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Topologic
    Tooltip: Returns an HSJSON string based on the input Topology and parameters
    """
    bl_idname = 'SvHSJSONByTopology'
    bl_label = 'EnergyModel.HSJSONByTopology'
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
        self.outputs.new('SvStringsSocket', 'HSJSON')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Replication",text="")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        modelList = self.inputs['Template Energy Model'].sv_get(deepcopy=True)
        weatherFileList = self.inputs['Weather File Path'].sv_get(deepcopy=True)
        ddyFileList = self.inputs['Design Day File Path'].sv_get(deepcopy=True)
        buildingTopologyList = self.inputs['Building Topology'].sv_get(deepcopy=True)
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
        buildingTopologyList = flatten(buildingTopologyList)
        shadingList = flatten(shadingList)
        #floorLevelsList does not need flattening
        buildingNameList = flatten(buildingNameList)
        buildingTypeList = flatten(buildingTypeList)
        defaultSpaceList = flatten(defaultSpaceList)
        northAxisList = flatten(northAxisList)
        glazingRatioList = flatten(glazingRatioList)
        coolingTempList = flatten(coolingTempList)
        heatingTempList = flatten(heatingTempList)
        inputs = [modelList, weatherFileList, ddyFileList, buildingTopologyList, shadingList, floorLevelsList, buildingNameList, buildingTypeList, defaultSpaceList, northAxisList, glazingRatioList, coolingTempList, heatingTempList]
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
        self.outputs['HSJSON].sv_set(outputs)

def register():
    bpy.utils.register_class(SvHSJSONByTopology)

def unregister():
    bpy.utils.unregister_class(SvHSJSONByTopology)
