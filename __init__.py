
bl_info = {
    "name": "Topologic-Sverchok",
    "author": "Wassim Jabi",
    "version": (0, 4, 0, 0),
    "blender": (2, 83, 0),
    "location": "Node Editor",
    "category": "Node",
    "description": "Topologic Sverchok",
    "warning": "",
    "wiki_url": "http://topologic.app",
    "tracker_url": "https://github.com/wassimj/topologicsverchok/issues"
}

import sys
import os, re
from os.path import expanduser
home = expanduser("~")
from sys import platform

topologicEgg = "topologic-0.3-py3.7.egg"
if platform == "linux" or platform == "linux2":
  dir = home+"/opt/anaconda3/envs/Blender377/lib/site-packages"
  for f in os.listdir(dir):
    if re.match('topologic', f):
      topologicEgg = f
  sys.path.append(home+"/opt/anaconda3/envs/Blender377/lib/site-packages")
  sys.path.append(home+"/opt/anaconda3/envs/Blender377/lib/site-packages/"+topologicEgg)
elif platform == "darwin":
  dir = home+"/opt/anaconda3/envs/Blender377/lib/site-packages"
  for f in os.listdir(dir):
    if re.match('topologic', f):
      topologicEgg = f
  sys.path.append(home+"/opt/anaconda3/envs/Blender377/lib/site-packages")
  sys.path.append(home+"/opt/anaconda3/envs/Blender377/lib/site-packages/"+topologicEgg)
elif platform == "win32":
  dir = home+"\\.conda\\envs\\Blender377\\lib\\site-packages"
  for f in os.listdir(dir):
    if re.match('topologic', f):
      topologicEgg = f
  sys.path.append(home+"\\.conda\\envs\\Blender377\\lib\\site-packages")
  sys.path.append(home+"\\.conda\\envs\\Blender377\\lib\\site-packages\\"+topologicEgg)

import importlib

import nodeitems_utils
import bl_operators

import sverchok
from sverchok.core import sv_registration_utils, make_node_list
from sverchok.utils import auto_gather_node_classes, get_node_class_reference
from sverchok.menu import SverchNodeItem, node_add_operators, SverchNodeCategory, register_node_panels, unregister_node_panels, unregister_node_add_operators
from sverchok.utils.extra_categories import register_extra_category_provider, unregister_extra_category_provider
from sverchok.ui.nodeview_space_menu import make_extra_category_menus
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
                ("Topologic.VertexType", "SvVertexType"),
                ("Topologic.EdgeByStartVertexEndVertex", "SvEdgeByStartVertexEndVertex"),
                ("Topologic.EdgeStartVertex", "SvEdgeStartVertex"),
                ("Topologic.EdgeEndVertex", "SvEdgeEndVertex"),
				("Topologic.EdgeVertexAtParameter", "SvEdgeVertexAtParameter"),
                ("Topologic.EdgeAdjacentEdges", "SvEdgeAdjacentEdges"),
                ("Topologic.EdgeSharedVertices", "SvEdgeSharedVertices"),
                ("Topologic.EdgeType", "SvEdgeType"),
                ("Topologic.WireByEdges", "SvWireByEdges"),
                ("Topologic.WireIsClosed", "SvWireIsClosed"),
                ("Topologic.WireType", "SvWireType"),
                ("Topologic.FaceByEdges", "SvFaceByEdges"),
				("Topologic.FaceByWire", "SvFaceByWire"),
                ("Topologic.FaceByWires", "SvFaceByWires"),
				("Topologic.FaceInternalVertex", "SvFaceInternalVertex"),
                ("Topologic.FaceType", "SvFaceType"),
                ("Topologic.ShellByFaces", "SvShellByFaces"),
				("Topologic.ShellType", "SvShellType"),
				("Topologic.CellByCuboid", "SvCellByCuboid"),
				("Topologic.CellByCylinder", "SvCellByCylinder"),
                ("Topologic.CellByFaces", "SvCellByFaces"),
				("Topologic.CellInternalVertex", "SvCellInternalVertex"),
				("Topologic.CellType", "SvCellType"),
                ("Topologic.CellComplexByFaces", "SvCellComplexByFaces"),
				("Topologic.CellComplexByCells", "SvCellComplexByCells"),
                ("Topologic.CellComplexType", "SvCellComplexType"),
                ("Topologic.ClusterByTopologies", "SvClusterByTopologies"),
                ("Topologic.ClusterType", "SvClusterType"),
                ("Topologic.TopologyByGeometry", "SvTopologyByGeometry"),
                ("Topologic.TopologyGeometry", "SvTopologyGeometry"),
				("Topologic.TopologyByString", "SvTopologyByString"),
				("Topologic.TopologyString", "SvTopologyString"),
				("Topologic.TopologySubTopologies", "SvTopologySubTopologies"),
                ("Topologic.TopologyVertices", "SvTopologyVertices"),
                ("Topologic.TopologyEdges", "SvTopologyEdges"),
                ("Topologic.TopologyWires", "SvTopologyWires"),
                ("Topologic.TopologyFaces", "SvTopologyFaces"),
                ("Topologic.TopologyShells", "SvTopologyShells"),
                ("Topologic.TopologyCells", "SvTopologyCells"),
                ("Topologic.TopologyCellComplexes", "SvTopologyCellComplexes"),
                ("Topologic.TopologySharedTopologies", "SvTopologySharedTopologies"),
                ("Topologic.TopologyBoolean", "SvTopologyBoolean"),
				("Topologic.TopologyTranslate", "SvTopologyTranslate"),
				("Topologic.TopologyRotate", "SvTopologyRotate"),
				("Topologic.TopologyScale", "SvTopologyScale"),
                ("Topologic.TopologyAddContents", "SvTopologyAddContents"),
                ("Topologic.TopologyContents", "SvTopologyContents"),
				("Topologic.TopologyCentroid", "SvTopologyCentroid"),
				("Topologic.TopologyCopy", "SvTopologyCopy"),
                ("Topologic.TopologyAnalyze", "SvTopologyAnalyze"),
				("Topologic.TopologyDictionary", "SvTopologyDictionary"),
                ("Topologic.TopologySetDictionary", "SvTopologySetDictionary"),
                ("Topologic.TopologySetDictionaries", "SvTopologySetDictionaries"),
				("Topologic.TopologyDecodeInformation", "SvTopologyDecodeInformation"),
				("Topologic.TopologyEncodeInformation", "SvTopologyEncodeInformation"),
                ("Topologic.DictionaryByKeysValues", "SvDictionaryByKeysValues"),
                ("Topologic.DictionaryValueAtKey", "SvDictionaryValueAtKey"),
                ("Topologic.DictionaryKeys", "SvDictionaryKeys"),
                ("Topologic.DictionaryValues", "SvDictionaryValues"),
				("Topologic.GraphByTopology", "SvGraphByTopology"),
				("Topologic.GraphShortestPath", "SvGraphShortestPath"),
				("Topologic.GraphTopology", "SvGraphTopology")
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
topologic_imported_modules = make_node_list()

reload_event = False

if "bpy" in locals():
    reload_event = True
    info("Reloading topologicsverchok...")
    reload_modules()

import bpy

def register_nodes():
    node_modules = make_node_list()
    for module in node_modules:
        module.register()
    info("Registered %s nodes", len(node_modules))

def unregister_nodes():
    global topologic_imported_modules
    for module in reversed(topologic_imported_modules):
        module.unregister()

def make_menu():
    menu = []
    index = nodes_index()
    for category, items in index:
        identifier = "TOPOLOGICSVERCHOK_" + category.replace(' ', '_')
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

our_menu_classes = []

def reload_modules():
    global topologic_imported_modules
    for im in topologic_imported_modules:
        debug("Reloading: %s", im)
        importlib.reload(im)

def register():
    global topologic_menu_classes

    debug("Registering toplogicsverchok")

    #settings.register()
    #icons.register()

    register_nodes()
    extra_nodes = importlib.import_module(".nodes", "topologicsverchok")
    auto_gather_node_classes(extra_nodes)
    menu = make_menu()
    menu_category_provider = SvExCategoryProvider("TOPOLOGICSVERCHOK", menu)
    register_extra_category_provider(menu_category_provider) #if 'TOPOLOGICSVERCHOK' in nodeitems_utils._node_categories:
        #unregister_node_panels()
        #nodeitems_utils.unregister_node_categories("TOPOLOGICSVERCHOK")
    nodeitems_utils.register_node_categories("TOPOLOGICSVERCHOK", menu)
    topologic_menu_classes = make_extra_category_menus()
    #register_node_panels("TOPOLOGICSVERCHOK", menu)
    #show_welcome()

def unregister():
    global topologic_menu_classes
    if 'TOPOLOGICSVERCHOK' in nodeitems_utils._node_categories:
        #unregister_node_panels()
        nodeitems_utils.unregister_node_categories("TOPOLOGICSVERCHOK")
    for clazz in topologic_menu_classes:
        try:
            bpy.utils.unregister_class(clazz)
        except Exception as e:
            print("Can't unregister menu class %s" % clazz)
            print(e)
    unregister_extra_category_provider("TOPOLOGICSVERCHOK")
    #unregister_node_add_operators()
    unregister_nodes()

    #icons.unregister()
    #settings.unregister()
