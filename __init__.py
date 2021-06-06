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
    "version": (0, 5, 7, 0),
    "blender": (2, 93, 0),
    "location": "Node Editor",
    "category": "Node",
    "description": "Topologic",
    "warning": "",
    "wiki_url": "http://topologic.app",
    "tracker_url": "https://github.com/wassimj/topologicsverchok/issues"
}

import sys
import os, re
from os.path import expanduser
from sys import platform
from os.path import expanduser
import bpy
home = expanduser("~")
blenderVersion =  "Blender"+str(bpy.app.version[0])+str(bpy.app.version[1])
if platform == 'win32':
  if os.path.exists('C:\\ProgramData\\anaconda3\\envs'):
    conda = 'C:\\ProgramData\\anaconda3\\envs'
  elif os.path.exists(home+'\\anaconda3\\envs'):
    conda = home+'\\anaconda3\\envs'
  else:
    raise Exception("Error: Could not find: "+home+'\\anaconda3\\envs nor '+'C:\\ProgramData\\anaconda3\\envs')
  sitePackages = '\\lib\\site-packages'
  blenderName = '\\'+[name for name in os.listdir(conda) if name.startswith(blenderVersion)][0]
  topologicEggName = '\\'+[name for name in os.listdir(conda+blenderName+sitePackages) if name.startswith('topologic')][0]
  if os.path.exists(conda+blenderName+sitePackages):
    sys.path.append(conda+blenderName+sitePackages)
  else:
    raise Exception("Error: Could not find "+conda+blenderName+sitePackages)
  if os.path.exists(conda+blenderName+sitePackages+topologicEggName):
    sys.path.append(conda+blenderName+sitePackages+topologicEggName)
  else:
    raise Exception("Error: Could not find "+conda+blenderName+sitePackages+topologicEggName)

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

from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import cppyy

# Bug in cppyy seems to be fixed. No need for this hack
#vertices = cppyy.gbl.std.list[Vertex.Ptr]()
#edges = cppyy.gbl.std.list[Edge.Ptr]()
#wires = cppyy.gbl.std.list[Wire.Ptr]()
#faces = cppyy.gbl.std.list[Face.Ptr]()
#shells = cppyy.gbl.std.list[Shell.Ptr]()
#cells = cppyy.gbl.std.list[Cell.Ptr]()
#cellcomplexes = cppyy.gbl.std.list[CellComplex.Ptr]()
#clusters = cppyy.gbl.std.list[Cluster.Ptr]()

#from topologicsverchok import icons
# make sverchok the root module name, (if sverchok dir not named exactly "sverchok")

if __name__ != "topologicsverchok":
    sys.modules["topologicsverchok"] = sys.modules[__name__]

def nodes_index():
	return [("Topologic", [
                ("Topologic.Version", "SvTopologicVersion"),
                ("Topologic.VertexByCoordinates", "SvVertexByCoordinates"),
                ("Topologic.VertexCoordinates", "SvVertexCoordinates"),
                ("Topologic.VertexDistance", "SvVertexDistance"),
                ("Topologic.VertexEnclosingCell", "SvVertexEnclosingCell"),
                ("Topologic.VertexNearestVertex", "SvVertexNearestVertex"),
                ("Topologic.VertexAdjacentEdges", "SvVertexAdjacentEdges"),
                ("Topologic.EdgeAdjacentFaces", "SvEdgeAdjacentFaces"),
                ("Topologic.EdgeAdjacentWires", "SvEdgeAdjacentWires"),
                ("Topologic.EdgeByStartVertexEndVertex", "SvEdgeByStartVertexEndVertex"),
                ("Topologic.EdgeByVertices", "SvEdgeByVertices"),
                ("Topologic.EdgeStartVertex", "SvEdgeStartVertex"),
                ("Topologic.EdgeEndVertex", "SvEdgeEndVertex"),
                ("Topologic.EdgeLength", "SvEdgeLength"),
                ("Topologic.EdgeParameterAtVertex", "SvEdgeParameterAtVertex"),
                ("Topologic.EdgeVertexAtParameter", "SvEdgeVertexAtParameter"),
                ("Topologic.EdgeAdjacentEdges", "SvEdgeAdjacentEdges"),
                ("Topologic.EdgeSharedVertices", "SvEdgeSharedVertices"),
                ("Topologic.WireAdjacentCells", "SvWireAdjacentCells"),
                ("Topologic.WireAdjacentShells", "SvWireAdjacentShells"),
                ("Topologic.WireByEdges", "SvWireByEdges"),
                ("Topologic.WireCircle", "SvWireCircle"),
                ("Topologic.WireCycles", "SvWireCycles"),
                ("Topologic.WireIsClosed", "SvWireIsClosed"),
                ("Topologic.WireRectangle", "SvWireRectangle"),
                ("Topologic.WireStar", "SvWireStar"),
                ("Topologic.FaceAddAperture", "SvFaceAddAperture"),
                ("Topologic.FaceAddInternalBoundary", "SvFaceAddInternalBoundary"),
                ("Topologic.FaceAdjacentCells", "SvFaceAdjacentCells"),
                ("Topologic.FaceAdjacentShells", "SvFaceAdjacentShells"),
                ("Topologic.FaceArea", "SvFaceArea"),
                ("Topologic.FaceByEdges", "SvFaceByEdges"),
                ("Topologic.FaceByWire", "SvFaceByWire"),
                ("Topologic.FaceByWires", "SvFaceByWires"),
                ("Topologic.FaceByVertices", "SvFaceByVertices"),
                ("Topologic.FaceExternalBoundary", "SvFaceExternalBoundary"),
                ("Topologic.FaceInternalVertex", "SvFaceInternalVertex"),
                ("Topologic.FaceIsInside", "SvFaceIsInside"),
                ("Topologic.FaceInternalBoundaries", "SvFaceInternalBoundaries"),
                ("Topologic.FaceNormalAtParameters", "SvFaceNormalAtParameters"),
                ("Topologic.FaceParametersAtVertex", "SvFaceParametersAtVertex"),
                ("Topologic.FaceTriangulate", "SvFaceTriangulate"),
                ("Topologic.FaceTrimByWire", "SvFaceTrimByWire"),
                ("Topologic.FaceVertexAtParameters", "SvFaceVertexAtParameters"),
                ("Topologic.ApertureByTopologyContext", "SvApertureByTopologyContext"),
                ("Topologic.ApertureTopology", "SvApertureTopology"),
                ("Topologic.ShellByFaces", "SvShellByFaces"),
                ("Topologic.ShellIsClosed", "SvShellIsClosed"),
                ("Topologic.CellAdjacentCells", "SvCellAdjacentCells"),
                ("Topologic.CellCylinder", "SvCellCylinder"),
                ("Topologic.CellByFaces", "SvCellByFaces"),
                ("Topologic.CellByLoft", "SvCellByLoft"),
                ("Topologic.CellByShell", "SvCellByShell"),
                ("Topologic.CellByThickenedFace", "SvCellByThickenedFace"),
                ("Topologic.CellExternalBoundary", "SvCellExternalBoundary"),
                ("Topologic.CellInternalBoundaries", "SvCellInternalBoundaries"),
                ("Topologic.CellInternalVertex", "SvCellInternalVertex"),
                ("Topologic.CellIsInside", "SvCellIsInside"),
                ("Topologic.CellPipe", "SvCellPipe"),
                ("Topologic.CellPrism", "SvCellPrism"),
                ("Topologic.CellVolume", "SvCellVolume"),
                ("Topologic.CellComplexByFaces", "SvCellComplexByFaces"),
                ("Topologic.CellComplexByCells", "SvCellComplexByCells"),
                ("Topologic.CellComplexExternalBoundary", "SvCellComplexExternalBoundary"),
                ("Topologic.CellComplexInternalBoundaries", "SvCellComplexInternalBoundaries"),
                ("Topologic.CellComplexNonManifoldFaces", "SvCellComplexNonManifoldFaces"),
                ("Topologic.ClusterByTopologies", "SvClusterByTopologies"),
                ("Topologic.ContextByTopologyParameters", "SvContextByTopologyParameters"),
                ("Topologic.ContextTopology", "SvContextTopology"),
                ("Topologic.TopologyAddApertures", "SvTopologyAddApertures"),
                ("Topologic.TopologyAddContent", "SvTopologyAddContent"),
                ("Topologic.TopologyAdjacentTopologies", "SvTopologyAdjacentTopologies"),
                ("Topologic.TopologyAnalyze", "SvTopologyAnalyze"),
                ("Topologic.TopologyApertures", "SvTopologyApertures"),
                ("Topologic.TopologyBoolean", "SvTopologyBoolean"),
                ("Topologic.TopologyBoundingBox", "SvTopologyBoundingBox"),
                ("Topologic.TopologyByGeometry", "SvTopologyByGeometry"),
                ("Topologic.TopologyByImportedBRep", "SvTopologyByImportedBRep"),
                ("Topologic.TopologyByString", "SvTopologyByString"),
                ("Topologic.TopologyCenterOfMass", "SvTopologyCenterOfMass"),
                ("Topologic.TopologyCentroid", "SvTopologyCentroid"),
                ("Topologic.TopologyContents", "SvTopologyContents"),
                ("Topologic.TopologyContexts", "SvTopologyContexts"),
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
                ("Topologic.TopologyOCCTShape", "SvTopologyOCCTShape"),
                ("Topologic.TopologyPlace", "SvTopologyPlace"),
                ("Topologic.TopologyRemoveCollinearEdges", "SvTopologyRemoveCollinearEdges"),
                ("Topologic.TopologyRemoveContents", "SvTopologyRemoveContents"),
                ("Topologic.TopologyRemoveCoplanarFaces", "SvTopologyRemoveCoplanarFaces"),
                ("Topologic.TopologyRotate", "SvTopologyRotate"),
                ("Topologic.TopologyScale", "SvTopologyScale"),
                ("Topologic.TopologySelectSubTopology", "SvTopologySelectSubTopology"),
                ("Topologic.TopologySelfMerge", "SvTopologySelfMerge"),
                ("Topologic.TopologySetDictionary", "SvTopologySetDictionary"),
                ("Topologic.TopologySharedTopologies", "SvTopologySharedTopologies"),
                ("Topologic.TopologyString", "SvTopologyString"),
                ("Topologic.TopologySubTopologies", "SvTopologySubTopologies"),
                ("Topologic.TopologyTransferDictionaries", "SvTopologyTransferDictionaries"),
                ("Topologic.TopologyTranslate", "SvTopologyTranslate"),
                ("Topologic.TopologyTriangulate", "SvTopologyTriangulate"),
                ("Topologic.TopologyTypeAsString", "SvTopologyTypeAsString"),
                ("Topologic.TopologyTypeID", "SvTopologyTypeID"),
                ("Topologic.DictionaryByKeysValues", "SvDictionaryByKeysValues"),
                ("Topologic.DictionaryByMergedDictionaries", "SvDictionaryByMergedDictionaries"),
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
                ("Topologic.GraphVerticesAtKeyValue", "SvGraphVerticesAtKeyValue")
                ]
                )]

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

import bpy

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
            ['SvVertexAdjacentEdges'],
            ['SvVertexByCoordinates'],
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
            ['SvEdgeAdjacentEdges'],
            ['SvEdgeByStartVertexEndVertex'],
            ['SvEdgeByVertices'],
            ['SvEdgeEndVertex'],
            ['SvEdgeLength'],
            ['SvEdgeParameterAtVertex'],
            ['SvEdgeSharedVertices'],
            ['SvEdgeStartVertex'],
            ['SvEdgeVertexAtParameter'],
        ])

make_class('TPSubcategoryEdge', 'Topologic @ Edge')

class NODEVIEW_MT_AddTPSubcategoryWire(bpy.types.Menu):
    bl_label = "TPSubcategoryWire"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryWire'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvWireAdjacentCells'],
            ['SvWireAdjacentShells'],
            ['SvWireByEdges'],
            ['SvWireCircle'],
            ['SvWireCycles'],
            ['SvWireIsClosed'],
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
            ['SvFaceAddAperture'],
            ['SvFaceAddInternalBoundary'],
            ['SvFaceAdjacentCells'],
            ['SvFaceAdjacentShells'],
            ['SvFaceArea'],
            ['SvFaceByEdges'],
            ['SvFaceByVertices'],
            ['SvFaceByWire'],
            ['SvFaceByWires'],
            ['SvFaceExternalBoundary'],
            ['SvFaceInternalBoundaries'],
            ['SvFaceInternalVertex'],
            ['SvFaceIsInside'],
            ['SvFaceNormalAtParameters'],
            ['SvFaceParametersAtVertex'],
            ['SvFaceTriangulate'],
            ['SvFaceTrimByWire'],
            ['SvFaceVertexAtParameters'],
        ])

make_class('TPSubcategoryFace', 'Topologic @ Face')

class NODEVIEW_MT_AddTPSubcategoryShell(bpy.types.Menu):
    bl_label = "TPSubcategoryShell"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryShell'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvShellByFaces'],
            ['SvShellIsClosed'],
        ])

make_class('TPSubcategoryShell', 'Topologic @ Shell')

class NODEVIEW_MT_AddTPSubcategoryCell(bpy.types.Menu):
    bl_label = "TPSubcategoryCell"
    bl_idname = 'NODEVIEW_MT_AddTPSubcategoryCell'

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, self.bl_label, [
            ['SvCellAdjacentCells'],
            ['SvCellByFaces'],
            ['SvCellCylinder'],
            ['SvCellByLoft'],
            ['SvCellByShell'],
            ['SvCellByThickenedFace'],
            ['SvCellExternalBoundary'],
            ['SvCellInternalBoundaries'],
            ['SvCellInternalVertex'],
            ['SvCellIsInside'],
            ['SvCellPipe'],
            ['SvCellPrism'],
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
			['SvTopologyByString'],
            ['SvTopologyCenterOfMass'],
            ['SvTopologyCentroid'],
            ['SvTopologyContents'],
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
            ['SvTopologyOCCTShape'],
            ['SvTopologyPlace'],
            ['SvTopologyRotate'],
            ['SvTopologyRemoveCollinearEdges'],
            ['SvTopologyRemoveContents'],
            ['SvTopologyRemoveCoplanarFaces'],
            ['SvTopologyScale'],
            ['SvTopologySelectSubTopology'],
            ['SvTopologySelfMerge'],
            ['SvTopologySetDictionary'],
            ['SvTopologySharedTopologies'],
            ['SvTopologyString'],
            ['SvTopologySubTopologies'],
            ['SvTopologyTransferDictionaries'],
            ['SvTopologyTranslate'],
            ['SvTopologyTriangulate'],
            ['SvTopologyTypeAsString'],
            ['SvTopologyTypeID'],
        ])
make_class('TPSubcategoryTopology', 'Topologic @ Topology')

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
			['@ Aperture'],
            ['@ Context'],
			['@ Dictionary'],
            ['@ Graph'],
            ['@ Topology'],
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
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryAperture)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryContext)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryDictionary)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryGraph)
    bpy.utils.register_class(NODEVIEW_MT_AddTPSubcategoryTopology)
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
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryAperture)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryContext)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryDictionary)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryGraph)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryTopology)
    bpy.utils.unregister_class(NODEVIEW_MT_AddTPSubcategoryAbout)
    #sockets.unregister()
    #icons.unregister()
    #settings.unregister()
