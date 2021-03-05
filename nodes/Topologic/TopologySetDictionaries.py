import bpy
from bpy.props import StringProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import cppyy
from collections import Iterable                            # < py38

# From: https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists
def flatten(items):
    """Yield items from any nested iterable; see Reference."""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x

def classByType(argument):
  switcher = {
    1: Vertex,
    2: Edge,
    4: Wire,
    8: Face,
    16: Shell,
    32: Cell,
    64: CellComplex,
    128: Cluster }
  return switcher.get(argument, Topology)

def fixTopologyClass(topology):
  topology.__class__ = classByType(topology.GetType())
  return topology

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output = recur(anItem)
	else:
		output = processItem(input)
	return output

def create_stl_list(cppyy_data_type):
    values = cppyy.gbl.std.list[cppyy_data_type]()
    return values

def convert_to_stl_list(py_list, cppyy_data_type):
    values = create_stl_list(cppyy_data_type)
    for i in py_list:
        values.push_back(i)
    return values

class SvTopologySetDictionaries(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Topologic
    Tooltip: Sets the input dictionaries for the sub-topologies of the input Topology using the input selector Vertices
    """
    bl_idname = 'SvTopologySetDictionaries'
    bl_label = 'Topology.SetDictionaries'
    TypeFilter: IntProperty(name="Type Filter", default=255, update=updateNode)
    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Topology')
        self.inputs.new('SvStringsSocket', 'Selectors')
        self.inputs.new('SvStringsSocket', 'Dictionaries')
        self.inputs.new('SvStringsSocket', 'Type Filter').prop_name = 'TypeFilter'
        self.outputs.new('SvStringsSocket', 'Topology')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        topology = flatten(self.inputs['Topology'].sv_get(deepcopy=False)[0])[0] #Consider only one Topology
        selectorList = flatten(self.inputs['Selectors'].sv_get(deepcopy=False)[0])
        dictionaryList = flatten(self.inputs['Dictionaries'].sv_get(deepcopy=False)[0])
        typeFilter = flatten(self.inputs['Type Filter'].sv_get(deepcopy=False)[0])[0] #Consider only one TypeFilter
        if len(selectorList) != len(dictionaryList):
            return
        selectors = convert_to_stl_list(selectorList, Vertex.Ptr)
        dictionaries = convert_to_stl_list(dictionaryList, Dictionary)
        result = topology.SetDictionaries(selectors, dictionaries, typeFilter)
        self.outputs['Topologies'].sv_set([result])

def register():
    bpy.utils.register_class(SvTopologySetDictionaries)

def unregister():
    bpy.utils.unregister_class(SvTopologySetDictionaries)
