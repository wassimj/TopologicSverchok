import bpy
from bpy.props import StringProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

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
		topology = self.inputs['Topology'].sv_get(deepcopy=False)[0] #Consider only one Topology
		selectorList = flatten(self.inputs['Selectors'].sv_get(deepcopy=False))
		dictionaryList = flatten(self.inputs['Dictionaries'].sv_get(deepcopy=False))
		typeFilter = self.inputs['Type Filter'].sv_get(deepcopy=False)[0][0] #Consider only one TypeFilter
		if len(selectorList) != len(dictionaryList):
			return
		selectors = convert_to_stl_list(selectorList, Vertex.Ptr)
		dictionaries = convert_to_stl_list(dictionaryList, Dictionary)
		for aDictionary in dictionaries:
			values = aDictionary.Values()
			returnList = []
			for aValue in values:
				s = cppyy.bind_object(aValue.Value(), 'StringStruct')
				returnList.append(str(s.getString))
			print(returnList)
		result = topology.SetDictionaries(selectors, dictionaries, typeFilter)
		result = fixTopologyClass(result)
		self.outputs['Topology'].sv_set([result])

def register():
	bpy.utils.register_class(SvTopologySetDictionaries)

def unregister():
	bpy.utils.unregister_class(SvTopologySetDictionaries)
