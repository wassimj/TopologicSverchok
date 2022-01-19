# * This file is part of Topologic software library.
# * Copyright(C) 2021, Cardiff University and University College London
# * 
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU Affero General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# * 
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU Affero General Public License for more details.
# * 
# * You should have received a copy of the GNU Affero General Public License
# * along with this program. If not, see <https://www.gnu.org/licenses/>.

bl_info = {
    "name": "Topologic",
    "author": "Wassim Jabi",
    "version": (0, 7, 0, 0),
    "blender": (3, 0, 0),
    "location": "Node Editor",
    "category": "Node",
    "description": "Topologic",
    "warning": "",
    "wiki_url": "http://topologic.app",
    "tracker_url": "https://github.com/wassimj/topologicsverchok/issues"
}

import sys
import os, re
from sys import platform
import bpy
blenderVersion =  "Blender"+str(bpy.app.version[0])+str(bpy.app.version[1])

sitePackagesFolderName = os.path.join(os.path.dirname(os.path.realpath(__file__)), "site-packages")
topologicFolderName = [filename for filename in os.listdir(sitePackagesFolderName) if filename.startswith("topologic")][0]
topologicPath = os.path.join(sitePackagesFolderName, topologicFolderName)
sys.path.append(topologicPath)
topologicPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "site-packages")
sys.path.append(topologicPath)

import importlib
import nodeitems_utils
import bl_operators
import sverchok
from sverchok.core import sv_registration_utils, make_node_list
from sverchok.utils import auto_gather_node_classes, get_node_class_reference
from sverchok.menu import SverchNodeItem, node_add_operators, SverchNodeCategory, register_node_panels, unregister_node_panels, unregister_node_add_operators
from sverchok.utils.extra_categories import register_extra_category_provider, unregister_extra_category_provider
from sverchok.ui.nodeview_space_menu import make_extra_category_menus, make_class, layout_draw_categories
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.logging import info, debug

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology


#from topologicsverchok import icons
# make sverchok the root module name, (if sverchok dir not named exactly "sverchok")

if __name__ != "topologicsverchok":
    sys.modules["topologicsverchok"] = sys.modules[__name__]

def nodes_index():
	coreNodes = [
                ("Topologic.Version", "SvTopologicVersion"),
                ("Topologic.VertexByCoordinates", "SvVertexByCoordinates"),
                ("Topologic.VertexByObjectLocation", "SvVertexByObjectLocation"),
                ("Topologic.VertexCoordinates", "SvVertexCoordinates"),
                ("Topologic.VertexDistance", "SvVertexDistance"),
                ("Topologic.VertexEnclosingCell", "SvVertexEnclosingCell"),
                ("Topologic.VertexNearestVertex", "SvVertexNearestVertex"),
                ("Topologic.EdgeByStartVertexEndVertex", "SvEdgeByStartVertexEndVertex"),
                ("Topologic.EdgeByVertices", "SvEdgeByVertices"),
                ("Topologic.EdgeDirection", "SvEdgeDirection"),
                ("Topologic.EdgeStartVertex", "SvEdgeStartVertex"),
                ("Topologic.EdgeEndVertex", "SvEdgeEndVertex"),
                ("Topologic.EdgeLength", "SvEdgeLength"),
                ("Topologic.EdgeParameterAtVertex", "SvEdgeParameterAtVertex"),
                ("Topologic.EdgeVertexByDistance", "SvEdgeVertexByDistance"),
                ("Topologic.EdgeVertexByParameter", "SvEdgeVertexByParameter"),
                ("Topologic.WireByEdges", "SvWireByEdges"),
                ("Topologic.WireCircle", "SvWireCircle"),
                ("Topologic.WireCycles", "SvWireCycles"),
                ("Topologic.WireIsClosed", "SvWireIsClosed"),
                ("Topologic.WireIsSimilar", "SvWireIsSimilar"),
                ("Topologic.WireLength", "SvWireLength"),
                ("Topologic.WireRectangle", "SvWireRectangle"),
                ("Topologic.WireStar", "SvWireStar"),
                ("Topologic.FaceAddFaceAsAperture", "SvFaceAddFaceAsAperture"),
                ("Topologic.FaceAddInternalBoundary", "SvFaceAddInternalBoundary"),
                ("Topologic.FaceArea", "SvFaceArea"),
                ("Topologic.FaceBoundingFace", "SvFaceBoundingFace"),
                ("Topologic.FaceByEdges", "SvFaceByEdges"),
                ("Topologic.FaceByWire", "SvFaceByWire"),
                ("Topologic.FaceByWires", "SvFaceByWires"),
                ("Topologic.FaceByVertices", "SvFaceByVertices"),
                ("Topologic.FaceCompactness", "SvFaceCompactness"),
                ("Topologic.FaceExternalBoundary", "SvFaceExternalBoundary"),
                ("Topologic.FaceFacingToward", "SvFaceFacingToward"),
                ("Topologic.FaceGridByDistances", "SvFaceGridByDistances"),
                ("Topologic.FaceGridByParameters", "SvFaceGridByParameters"),
                ("Topologic.FaceInternalVertex", "SvFaceInternalVertex"),
                ("Topologic.FaceIsInside", "SvFaceIsInside"),
                ("Topologic.FaceInternalBoundaries", "SvFaceInternalBoundaries"),
                ("Topologic.FaceNormalAtParameters", "SvFaceNormalAtParameters"),
                ("Topologic.FaceParametersAtVertex", "SvFaceParametersAtVertex"),
                ("Topologic.FaceTrimByWire", "SvFaceTrimByWire"),
                ("Topologic.FaceVertexByParameters", "SvFaceVertexByParameters"),
                ("Topologic.ApertureByTopologyContext", "SvApertureByTopologyContext"),
                ("Topologic.ApertureTopology", "SvApertureTopology"),
                ("Topologic.ShellByFaces", "SvShellByFaces"),
                ("Topologic.ShellExternalBoundary", "SvShellExternalBoundary"),
                ("Topologic.ShellInternalBoundaries", "SvShellInternalBoundaries"),
                ("Topologic.ShellIsClosed", "SvShellIsClosed"),
                ("Topologic.CellCone", "SvCellCone"),
                ("Topologic.CellCylinder", "SvCellCylinder"),
                ("Topologic.CellByFaces", "SvCellByFaces"),
                ("Topologic.CellByLoft", "SvCellByLoft"),
                ("Topologic.CellByShell", "SvCellByShell"),
                ("Topologic.CellByThickenedFace", "SvCellByThickenedFace"),
                ("Topologic.CellCompactness", "SvCellCompactness"),
                ("Topologic.CellExternalBoundary", "SvCellExternalBoundary"),
                ("Topologic.CellInternalBoundaries", "SvCellInternalBoundaries"),
                ("Topologic.CellInternalVertex", "SvCellInternalVertex"),
                ("Topologic.CellIsInside", "SvCellIsInside"),
                ("Topologic.CellPipe", "SvCellPipe"),
                ("Topologic.CellPrism", "SvCellPrism"),
                ("Topologic.CellSets", "SvCellSets"),
                ("Topologic.CellSuperCells", "SvCellSuperCells"),
                ("Topologic.CellSurfaceArea", "SvCellSurfaceArea"),
                ("Topologic.CellVolume", "SvCellVolume"),
                ("Topologic.CellComplexByFaces", "SvCellComplexByFaces"),
                ("Topologic.CellComplexByCells", "SvCellComplexByCells"),
                ("Topologic.CellComplexDecompose", "SvCellComplexDecompose"),
                ("Topologic.CellComplexExternalBoundary", "SvCellComplexExternalBoundary"),
                ("Topologic.CellComplexInternalBoundaries", "SvCellComplexInternalBoundaries"),
                ("Topologic.CellComplexNonManifoldFaces", "SvCellComplexNonManifoldFaces"),
                ("Topologic.ClusterByTopologies", "SvClusterByTopologies"),
                ("Topologic.ContextByTopologyParameters", "SvContextByTopologyParameters"),
                ("Topologic.ContextTopology", "SvContextTopology"),
                ("Topologic.TopologyAddApertures", "SvTopologyAddApertures"),
                ("Topologic.TopologyAddContent", "SvTopologyAddContent"),
                ("Topologic.TopologyAddDictionary", "SvTopologyAddDictionary"),
                ("Topologic.TopologyAdjacentTopologies", "SvTopologyAdjacentTopologies"),
                ("Topologic.TopologyAnalyze", "SvTopologyAnalyze"),
                ("Topologic.TopologyApertures", "SvTopologyApertures"),
                ("Topologic.TopologyBoolean", "SvTopologyBoolean"),
                ("Topologic.TopologyBoundingBox", "SvTopologyBoundingBox"),
                ("Topologic.TopologyByGeometry", "SvTopologyByGeometry"),
                ("Topologic.TopologyByImportedBRep", "SvTopologyByImportedBRep"),
                ("Topologic.TopologyByOCCTShape", "SvTopologyByOCCTShape"),
                ("Topologic.TopologyByString", "SvTopologyByString"),
                ("Topologic.TopologyCenterOfMass", "SvTopologyCenterOfMass"),
                ("Topologic.TopologyCentroid", "SvTopologyCentroid"),
                ("Topologic.TopologyContent", "SvTopologyContent"),
                ("Topologic.TopologyContext", "SvTopologyContext"),
                ("Topologic.TopologyCopy", "SvTopologyCopy"),
                ("Topologic.TopologyDecodeInformation", "SvTopologyDecodeInformation"),
                ("Topologic.TopologyDictionary", "SvTopologyDictionary"),
                ("Topologic.TopologyDimensionality", "SvTopologyDimensionality"),
                ("Topologic.TopologyDivide", "SvTopologyDivide"),
                ("Topologic.TopologyEncodeInformation", "SvTopologyEncodeInformation"),
                ("Topologic.TopologyExplode", "SvTopologyExplode"),
                ("Topologic.TopologyExportToBRep", "SvTopologyExportToBRep"),
                ("Topologic.TopologyFilter", "SvTopologyFilter"),
                ("Topologic.TopologyGeometry", "SvTopologyGeometry"),
                ("Topologic.TopologyIsSame", "SvTopologyIsSame"),
                ("Topologic.TopologyMergeAll", "SvTopologyMergeAll"),
                ("Topologic.TopologyOCCTShape", "SvTopologyOCCTShape"),
                ("Topologic.TopologyPlace", "SvTopologyPlace"),
                ("Topologic.TopologyRemoveCollinearEdges", "SvTopologyRemoveCollinearEdges"),
                ("Topologic.TopologyRemoveContent", "SvTopologyRemoveContent"),
                ("Topologic.TopologyRotate", "SvTopologyRotate"),
                ("Topologic.TopologyScale", "SvTopologyScale"),
                ("Topologic.TopologySelectSubTopology", "SvTopologySelectSubTopology"),
                ("Topologic.TopologySelfMerge", "SvTopologySelfMerge"),
                ("Topologic.TopologySetDictionary", "SvTopologySetDictionary"),
                ("Topologic.TopologySharedTopologies", "SvTopologySharedTopologies"),
                ("Topologic.TopologyString", "SvTopologyString"),
                ("Topologic.TopologySubTopologies", "SvTopologySubTopologies"),
                ("Topologic.TopologySuperTopologies", "SvTopologySuperTopologies"),
                ("Topologic.TopologyTransferDictionaries", "SvTopologyTransferDictionaries"),
                ("Topologic.TopologyTransferDictionariesBySelectors", "SvTopologyTransferDictionariesBySelectors"),
                ("Topologic.TopologyTransform", "SvTopologyTransform"),
                ("Topologic.TopologyTranslate", "SvTopologyTranslate"),
                ("Topologic.TopologyTriangulate", "SvTopologyTriangulate"),
                ("Topologic.TopologyType", "SvTopologyType"),
                ("Topologic.TopologyTypeID", "SvTopologyTypeID"),
                ("Topologic.DictionaryByKeysValues", "SvDictionaryByKeysValues"),
                ("Topologic.DictionaryByMergedDictionaries", "SvDictionaryByMergedDictionaries"),
                ("Topologic.DictionaryByObjectProperties", "SvDictionaryByObjectProperties"),
                ("Topologic.DictionaryValueAtKey", "SvDictionaryValueAtKey"),
                ("Topologic.DictionaryKeys", "SvDictionaryKeys"),
                ("Topologic.DictionaryValues", "SvDictionaryValues"),
                ("Topologic.GraphAddEdge", "SvGraphAddEdge"),
                ("Topologic.GraphAddVertex", "SvGraphAddVertex"),
                ("Topologic.GraphAdjacentVertices", "SvGraphAdjacentVertices"),
                ("Topologic.GraphAllPaths", "SvGraphAllPaths"),
                ("Topologic.GraphByTopology", "SvGraphByTopology"),
                ("Topologic.GraphConnect", "SvGraphConnect"),
                ("Topologic.GraphContainsEdge", "SvGraphContainsEdge"),
                ("Topologic.GraphContainsVertex", "SvGraphContainsVertex"),
                ("Topologic.GraphDegreeSequence", "SvGraphDegreeSequence"),
                ("Topologic.GraphDensity", "SvGraphDensity"),
                ("Topologic.GraphDepthMap", "SvGraphDepthMap"),
                ("Topologic.GraphDiameter", "SvGraphDiameter"),
                ("Topologic.GraphEdge", "SvGraphEdge"),
                ("Topologic.GraphEdges", "SvGraphEdges"),
                ("Topologic.GraphIsComplete", "SvGraphIsComplete"),
                ("Topologic.GraphIsErdoesGallai", "SvGraphIsErdoesGallai"),
                ("Topologic.GraphIsolatedVertices", "SvGraphIsolatedVertices"),
                ("Topologic.GraphMaximumDelta", "SvGraphMaximumDelta"),
                ("Topologic.GraphMinimumDelta", "SvGraphMinimumDelta"),
				("Topologic.GraphMST", "SvGraphMST"),
				("Topologic.GraphNearestVertex", "SvGraphNearestVertex"),
				("Topologic.GraphPath", "SvGraphPath"),
                ("Topologic.GraphRemoveEdge", "SvGraphRemoveEdge"),
                ("Topologic.GraphRemoveVertex", "SvGraphRemoveVertex"),
                ("Topologic.GraphShortestPath", "SvGraphShortestPath"),
                ("Topologic.GraphShortestPaths", "SvGraphShortestPaths"),
                ("Topologic.GraphTopologicalDistance", "SvGraphTopologicalDistance"),
                ("Topologic.GraphTopology", "SvGraphTopology"),
                ("Topologic.GraphVertexDegree", "SvGraphVertexDegree"),
                ("Topologic.GraphVertices", "SvGraphVertices"),
                ("Topologic.GraphVerticesAtKeyValue", "SvGraphVerticesAtKeyValue"),
                ("Topologic.ColorByValueInRange", "SvColorByValueInRange")]
	numpyNodes = [("Topologic.TopologyRemoveCoplanarFaces", "SvTopologyRemoveCoplanarFaces")]
	ifcNodes = [("Topologic.TopologyByImportedIFC", "SvTopologyByImportedIFC")]
	web3Nodes = [("Topologic.ContractByParameters", "SvContractByParameters")]
	ipfsNodes = [("Topologic.TopologyByImportedIPFS", "SvTopologyByImportedIPFS"),
                 ("Topologic.TopologyExportToIPFS", "SvTopologyExportToIPFS")]
	openstudioNodes = [("Topologic.EnergyModelByImportedOSM", "SvEnergyModelByImportedOSM"),
                ("Topologic.EnergyModelByTopology", "SvEnergyModelByTopology"),
                ("Topologic.EnergyModelColumnNames", "SvEnergyModelColumnNames"),
                ("Topologic.EnergyModelDefaultConstructionSets", "SvEnergyModelDefaultConstructionSets"),
                ("Topologic.EnergyModelDefaultScheduleSets", "SvEnergyModelDefaultScheduleSets"),
                ("Topologic.EnergyModelExportToGbXML", "SvEnergyModelExportToGbXML"),
                ("Topologic.EnergyModelExportToOSM", "SvEnergyModelExportToOSM"),
                ("Topologic.EnergyModelQuery", "SvEnergyModelQuery"),
                ("Topologic.EnergyModelReportNames", "SvEnergyModelReportNames"),
                ("Topologic.EnergyModelRowNames", "SvEnergyModelRowNames"),
                ("Topologic.EnergyModelRunSimulation", "SvEnergyModelRunSimulation"),
                ("Topologic.EnergyModelSpaceTypes", "SvEnergyModelSpaceTypes"),
                ("Topologic.EnergyModelSqlFile", "SvEnergyModelSqlFile"),
                ("Topologic.EnergyModelTableNames", "SvEnergyModelTableNames"),
                ("Topologic.EnergyModelTopologies", "SvEnergyModelTopologies"),
                ("Topologic.EnergyModelUnits", "SvEnergyModelUnits")]
	honeybeeNodes = [("Topologic.HBModelByTopology", "SvHBModelByTopology"),
                ("Topologic.HBModelExportToHBJSON", "SvHBModelExportToHBJSON"),
                ("Topologic.HBModelString", "SvHBModelString"),
                ("Topologic.HBConstructionSetByIdentifier", "SvHBConstructionSetByIdentifier"),
                ("Topologic.HBConstructionSets", "SvHBConstructionSets"),
                ("Topologic.HBProgramTypeByIdentifier", "SvHBProgramTypeByIdentifier"),
                ("Topologic.HBProgramTypes", "SvHBProgramTypes")]
	neo4jNodes = [("Topologic.Neo4jGraphAddTopologicGraph", "SvNeo4jGraphAddTopologicGraph"),
                ("Topologic.Neo4jGraphByParameters", "SvNeo4jGraphByParameters"),
                ("Topologic.Neo4jGraphDeleteAll", "SvNeo4jGraphDeleteAll")]
	osifcNodes = [("Topologic.EnergyModelByImportedIFC", "SvEnergyModelByImportedIFC")]
	osifc = 0

	try:
		import numpy
		coreNodes = coreNodes+numpyNodes
	except:
		print("Topologic - Warning: Could not import numpy so some related nodes are not available.")
	try:
		import ifcopenshell
		coreNodes = coreNodes+ifcNodes
		osifc = osifc + 1
	except:
		print("Topologic - Warning: Could not import ifcopenshell so some related nodes are not available.")
	try:
		import ipfshttpclient
		coreNodes = coreNodes+ipfsNodes
	except:
		print("Topologic - Warning: Could not import ipfshttpclient so some related nodes are not available.")
	try:
		import web3
		coreNodes = coreNodes+web3Nodes
	except:
		print("Topologic - Warning: Could not import web3 so some related nodes are not available.")
	try:
		import openstudio
		coreNodes = coreNodes+openstudioNodes
		osifc = osifc + 1
	except:
		print("Topologic - Warning: Could not import openstudio so some related nodes are not available.")
	try:
		import honeybee
		import honeybee_energy
		import ladybug
		import json
		coreNodes = coreNodes+honeybeeNodes
	except:
		print("Topologic - Warning: Could not import ladybug/honeybee/json so some related nodes are not available.")
	try:
		import py2neo
		coreNodes = coreNodes+neo4jNodes
	except:
		print("Topologic - Warning: Could not import py2neo so some related nodes are not available.")
	if osifc > 1:
		coreNodes = coreNodes+osifcNodes
	else:
		print("Topologic - Warning: Could not import either openstudio or ifcopenshell so some related nodes that require both to be installed are not available.")

	return [("Topologic", coreNodes)]

def make_node_list():
    modules = []
    base_name = "topologicsverchok.nodes"
    index = nodes_index()
    for category, items in index:
        for module_name, node_name in items:
            module = importlib.import_module(f".{module_name}", base_name)
            modules.append(module)
    return modules

#imported_modules = [icons] + make_node_list()
imported_modules = make_node_list()

reload_event = False

def register_nodes():
	node_modules = make_node_list()
	for module in node_modules:
		module.register()
	#info("Registered %s nodes", len(node_modules))

def unregister_nodes():
	global imported_modules
	for module in reversed(imported_modules):
		module.unregister()

def make_menu():
    menu = []
    index = nodes_index()
    for category, items in index:
        identifier = "TOPOLOGIC_" + category.replace(' ', '_')
        node_items = []
        for item in items:
            nodetype = item[1]
            rna = get_node_class_reference(nodetype)
            if not rna:
                info("Node `%s' is not available (probably due to missing dependencies).", nodetype)
            else:
                node_item = SverchNodeItem.new(nodetype)
                node_items.append(node_item)
        if node_items:
            cat = SverchNodeCategory(
                        identifier,
                        category,
                        items=node_items
                    )
            menu.append(cat)
    return menu

class SvExCategoryProvider(object):
    def __init__(self, identifier, menu):
        self.identifier = identifier
        self.menu = menu

    def get_categories(self):
        return self.menu

topologic_menu_classes = []

class NODEVIEW_MT_AddTPSubcategoryAbout(bpy.types.Menu):
    bl_label = "TPSubcategoryAbout"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryAbout'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvTopologicVersion'],
        ])

make_class('TPSubcategoryAbout', 'Topologic @ About')

class NODEVIEW_MT_AddTPSubcategoryVertex(bpy.types.Menu):
    bl_label = "TPSubcategoryVertex"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryVertex'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvVertexByCoordinates'],
            ['SvVertexByObjectLocation'],
            ['SvVertexCoordinates'],
            ['SvVertexDistance'],
            ['SvVertexEnclosingCell'],
            ['SvVertexNearestVertex'],
        ])

make_class('TPSubcategoryVertex', 'Topologic @ Vertex')

class NODEVIEW_MT_AddTPSubcategoryEdge(bpy.types.Menu):
    bl_label = "TPSubcategoryEdge"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryEdge'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvEdgeByStartVertexEndVertex'],
            ['SvEdgeByVertices'],
            ['SvEdgeDirection'],
            ['SvEdgeEndVertex'],
            ['SvEdgeLength'],
            ['SvEdgeParameterAtVertex'],
            ['SvEdgeSharedVertices'],
            ['SvEdgeStartVertex'],
            ['SvEdgeVertexByDistance'],
            ['SvEdgeVertexByParameter'],
        ])

make_class('TPSubcategoryEdge', 'Topologic @ Edge')

class NODEVIEW_MT_AddTPSubcategoryWire(bpy.types.Menu):
    bl_label = "TPSubcategoryWire"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryWire'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvWireByEdges'],
            ['SvWireCircle'],
            ['SvWireCycles'],
            ['SvWireIsClosed'],
            ['SvWireIsSimilar'],
            ['SvWireLength'],
            ['SvWireRectangle'],
            ['SvWireStar'],
        ])

make_class('TPSubcategoryWire', 'Topologic @ Wire')

class NODEVIEW_MT_AddTPSubcategoryFace(bpy.types.Menu):
    bl_label = "TPSubcategoryFace"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryFace'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvFaceAddFaceAsAperture'],
            ['SvFaceAddInternalBoundary'],
            ['SvFaceArea'],
            ['SvFaceBoundingFace'],
            ['SvFaceByEdges'],
            ['SvFaceByVertices'],
            ['SvFaceByWire'],
            ['SvFaceByWires'],
            ['SvFaceCompactness'],
            ['SvFaceExternalBoundary'],
            ['SvFaceFacingToward'],
            ['SvFaceGridByDistances'],
            ['SvFaceGridByParameters'],
            ['SvFaceInternalBoundaries'],
            ['SvFaceInternalVertex'],
            ['SvFaceIsInside'],
            ['SvFaceNormalAtParameters'],
            ['SvFaceParametersAtVertex'],
            ['SvFaceTriangulate'],
            ['SvFaceTrimByWire'],
            ['SvFaceVertexByParameters'],
        ])

make_class('TPSubcategoryFace', 'Topologic @ Face')

class NODEVIEW_MT_AddTPSubcategoryShell(bpy.types.Menu):
    bl_label = "TPSubcategoryShell"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryShell'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvShellByFaces'],
            ['SvShellExternalBoundary'],
            ['SvShellInternalBoundaries'],
            ['SvShellIsClosed'],
        ])

make_class('TPSubcategoryShell', 'Topologic @ Shell')

class NODEVIEW_MT_AddTPSubcategoryCell(bpy.types.Menu):
    bl_label = "TPSubcategoryCell"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryCell'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvCellByFaces'],
            ['SvCellCone'],
            ['SvCellCylinder'],
            ['SvCellByLoft'],
            ['SvCellByShell'],
            ['SvCellByThickenedFace'],
            ['SvCellCompactness'],
            ['SvCellExternalBoundary'],
            ['SvCellInternalBoundaries'],
            ['SvCellInternalVertex'],
            ['SvCellIsInside'],
            ['SvCellPipe'],
            ['SvCellPrism'],
            ['SvCellSets'],
            ['SvCellSuperCells'],
            ['SvCellSurfaceArea'],
            ['SvCellVolume'],
        ])

make_class('TPSubcategoryCell', 'Topologic @ Cell')

class NODEVIEW_MT_AddTPSubcategoryCellComplex(bpy.types.Menu):
    bl_label = "TPSubcategoryCellComplex"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryCellComplex'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvCellComplexByCells'],
            ['SvCellComplexByFaces'],
            ['SvCellComplexDecompose'],
            ['SvCellComplexExternalBoundary'],
            ['SvCellComplexInternalBoundaries'],
            ['SvCellComplexNonManifoldFaces'],
        ])

make_class('TPSubcategoryCellComplex', 'Topologic @ CellComplex')

class NODEVIEW_MT_AddTPSubcategoryCluster(bpy.types.Menu):
    bl_label = "TPSubcategoryCluster"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryCluster'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvClusterByTopologies'],
        ])

make_class('TPSubcategoryCluster', 'Topologic @ Cluster')

class NODEVIEW_MT_AddTPSubcategoryAperture(bpy.types.Menu):
    bl_label = "TPSubcategoryAperture"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryAperture'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvApertureByTopologyContext'],
            ['SvApertureTopology'],
        ])

make_class('TPSubcategoryAperture', 'Topologic @ Aperture')

class NODEVIEW_MT_AddTPSubcategoryGraph(bpy.types.Menu):
    bl_label = "TPSubcategoryGraph"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryGraph'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvGraphAddEdge'],
            ['SvGraphAddVertex'],
            ['SvGraphAdjacentVertices'],
            ['SvGraphAllPaths'],
            ['SvGraphByTopology'],
            ['SvGraphConnect'],
            ['SvGraphContainsEdge'],
            ['SvGraphContainsVertex'],
            ['SvGraphDegreeSequence'],
            ['SvGraphDensity'],
            ['SvGraphDepthMap'],
            ['SvGraphDiameter'],
            ['SvGraphEdge'],
            ['SvGraphEdges'],
            ['SvGraphIsComplete'],
            ['SvGraphIsErdoesGallai'],
            ['SvGraphIsolatedVertices'],
            ['SvGraphMaximumDelta'],
            ['SvGraphMinimumDelta'],
            ['SvGraphMST'],
            ['SvGraphNearestVertex'],
            ['SvGraphPath'],
            ['SvGraphRemoveEdge'],
            ['SvGraphRemoveVertex'],
            ['SvGraphShortestPath'],
            ['SvGraphShortestPaths'],
            ['SvGraphTopologicalDistance'],
            ['SvGraphTopology'],
            ['SvGraphVertexDegree'],
            ['SvGraphVertices'],
            ['SvGraphVerticesAtKeyValue'],
        ])

make_class('TPSubcategoryGraph', 'Topologic @ Graph')

class NODEVIEW_MT_AddTPSubcategoryDictionary(bpy.types.Menu):
    bl_label = "TPSubcategoryDictionary"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryDictionary'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvDictionaryByKeysValues'],
            ['SvDictionaryByMergedDictionaries'],
            ['SvDictionaryByObjectProperties'],
            ['SvDictionaryValueAtKey'],
            ['SvDictionaryKeys'],
            ['SvDictionaryValues'],
        ])

make_class('TPSubcategoryDictionary', 'Topologic @ Dictionary')

class NODEVIEW_MT_AddTPSubcategoryContext(bpy.types.Menu):
    bl_label = "TPSubcategoryContext"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryContext'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvContextByTopologyParameters'],
            ['SvContextTopology'],
        ])

make_class('TPSubcategoryContext', 'Topologic @ Context')

class NODEVIEW_MT_AddTPSubcategoryTopology(bpy.types.Menu):
    bl_label = "TPSubcategoryTopology"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryTopology'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvTopologyAddApertures'],
            ['SvTopologyAddContent'],
            ['SvTopologyAdjacentTopologies'],
            ['SvTopologyAnalyze'],
            ['SvTopologyApertures'],
            ['SvTopologyBoolean'],
            ['SvTopologyBoundingBox'],
            ['SvTopologyByGeometry'],
            ['SvTopologyByImportedBRep'],
            ['SvTopologyByOCCTShape'],
			['SvTopologyByString'],
            ['SvTopologyCenterOfMass'],
            ['SvTopologyCentroid'],
            ['SvTopologyContent'],
            ['SvTopologyContexts'],
            ['SvTopologyCopy'],
            ['SvTopologyDecodeInformation'],
            ['SvTopologyDictionary'],
            ['SvTopologyDimensionality'],
            ['SvTopologyDivide'],
            ['SvTopologyEncodeInformation'],
            ['SvTopologyExplode'],
            ['SvTopologyExportToBRep'],
            ['SvTopologyFilter'],
            ['SvTopologyGeometry'],
            ['SvTopologyIsSame'],
            ['SvTopologyMergeAll'],
            ['SvTopologyOCCTShape'],
            ['SvTopologyPlace'],
            ['SvTopologyRotate'],
            ['SvTopologyRemoveCollinearEdges'],
            ['SvTopologyRemoveContent'],
            ['SvTopologyRemoveCoplanarFaces'],
            ['SvTopologyScale'],
            ['SvTopologySelectSubTopology'],
            ['SvTopologySelfMerge'],
            ['SvTopologySetDictionary'],
            ['SvTopologySharedTopologies'],
            ['SvTopologyString'],
            ['SvTopologySubTopologies'],
            ['SvTopologySuperTopologies'],
            ['SvTopologyTransferDictionaries'],
            ['SvTopologyTransferDictionariesBySelectors'],
            ['SvTopologyTransform'],
            ['SvTopologyTranslate'],
            ['SvTopologyTriangulate'],
            ['SvTopologyType'],
            ['SvTopologyTypeID'],
        ])
make_class('TPSubcategoryTopology', 'Topologic @ Topology')

class NODEVIEW_MT_AddTPSubcategoryColor(bpy.types.Menu):
    bl_label = "TPSubcategoryColor"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryColor'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvColorByValueInRange'],
        ])

make_class('TPSubcategoryColor', 'Topologic @ Color')

class NODEVIEW_MT_AddTPSubcategoryEnergyModel(bpy.types.Menu):
    bl_label = "TPSubcategoryEnergyModel"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryEnergyModel'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvEnergyModelByImportedIFC'],
            ['SvEnergyModelByImportedOSM'],
            ['SvEnergyModelByTopology'],
            ['SvHBJSONByTopology'],
            ['SvEnergyModelExportToHBJSON'],
            ['SvEnergyModelColumnNames'],
            ['SvEnergyModelDefaultConstructionSets'],
            ['SvEnergyModelDefaultScheduleSets'],
            ['SvEnergyModelExportToGbXML'],
            ['SvEnergyModelExportToOSM'],
            ['SvEnergyModelQuery'],
            ['SvEnergyModelReportNames'],
            ['SvEnergyModelRowNames'],
            ['SvEnergyModelRunSimulation'],
            ['SvEnergyModelSpaceTypes'],
            ['SvEnergyModelSqlFile'],
            ['SvEnergyModelTableNames'],
            ['SvEnergyModelTopologies'],
            ['SvEnergyModelUnits'],
        ])

make_class('TPSubcategoryEnergyModel', 'Topologic @ Openstudio')

class NODEVIEW_MT_AddTPSubcategoryHBModel(bpy.types.Menu):
    bl_label = "TPSubcategoryHBModel"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryHBModel'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvHBModelByTopology'],
            ['SvHBModelExportToHBJSON'],
            ['SvHBModelString'],
            ['SvHBConstructionSetByIdentifier'],
            ['SvHBConstructionSets'],
            ['SvHBProgramTypeByIdentifier'],
            ['SvHBProgramTypes']
        ])

make_class('TPSubcategoryHBModel', 'Topologic @ Honeybee')

class NODEVIEW_MT_AddTPSubcategoryIFC(bpy.types.Menu):
    bl_label = "TPSubcategoryIFC"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryIFC'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvEnergyModelByImportedIFC'],
            ['SvTopologyByImportedIFC'],
        ])

make_class('TPSubcategoryIFC', 'Topologic @ IFC')

class NODEVIEW_MT_AddTPSubcategoryBlockchain(bpy.types.Menu):
    bl_label = "TPSubcategoryBlockchain"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryBlockchain'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvContractByParameters'],
            ['SvTopologyByImportedIPFS'],
            ['SvTopologyExportToIPFS'],
        ])

make_class('TPSubcategoryBlockchain', 'Topologic @ Blockchain')

class NODEVIEW_MT_AddTPSubcategoryNeo4j(bpy.types.Menu):
    bl_label = "TPSubcategoryNeo4j"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryNeo4j'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvNeo4jGraphAddTopologicGraph'],
            ['SvNeo4jGraphByParameters'],
            ['SvNeo4jGraphDeleteAll'],
        ])

make_class('TPSubcategoryNeo4j', 'Topologic @ Neo4j')
# Main menu
class NODEVIEW_MT_EX_TOPOLOGIC_Topologic(bpy.types.Menu):
    bl_label = 'Topologic'

    def draw(self, context):
        layout_draw_categories(self.layout, 'Topologic', [
            ['@ Vertex'],
            ['@ Edge'],
            ['@ Wire'],
            ['@ Face'],
            ['@ Shell'],
            ['@ Cell'],
            ['@ CellComplex'],
            ['@ Cluster'],
            ['@ Topology'],
			['@ Aperture'],
            ['@ Color'],
            ['@ Context'],
			['@ Dictionary'],
            ['@ Graph'],
            ['@ Openstudio'],
            ['@ Honeybee'],
            ['@ IFC'],
            ['@ Blockchain'],
            ['@ Neo4j'],
            ['@ About'],
        ])

def register():
    global topologic_menu_classes

    #debug("Registering Topologic")

    #settings.register()
    #icons.register()
    #sockets.register()
    bpy.utils.register_class(NODEVIEW_MT_EX_TOPOLOGIC_Topologic)
    register_nodes()
    extra_nodes = importlib.import_module(".nodes", "topologicsverchok")
    auto_gather_node_classes(extra_nodes)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryVertex)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryEdge)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryWire)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryFace)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryShell)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryCell)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryCellComplex)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryCluster)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryTopology)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryAperture)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryColor)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryContext)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryDictionary)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryGraph)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryEnergyModel)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryHBModel)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryIFC)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryBlockchain)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryNeo4j)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryAbout)
    menu = make_menu()
    menu_category_provider = SvExCategoryProvider("TOPOLOGIC", menu)
    register_extra_category_provider(menu_category_provider)
    nodeitems_utils.register_node_categories("TOPOLOGIC", menu)

def unregister():
    global topologic_menu_classes
    if 'TOPOLOGIC' in nodeitems_utils._node_categories:
        #unregister_node_panels()
        nodeitems_utils.unregister_node_categories("TOPOLOGIC")
    for clazz in topologic_menu_classes:
        try:
            bpy.utils.unregister_class(clazz)
        except Exception as e:
            print("Can't unregister menu class %s" % clazz)
            print(e)
    unregister_extra_category_provider("TOPOLOGIC")
    unregister_nodes()
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryVertex)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryEdge)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryWire)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryFace)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryShell)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryCell)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryCellComplex)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryCluster)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryTopology)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryAperture)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryColor)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryContext)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryDictionary)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryGraph)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryEnergyModel)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryHBModel)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryIFC)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryBlockchain)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryNeo4j)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryAbout)
    #sockets.unregister()
    #icons.unregister()
    #settings.unregister()
