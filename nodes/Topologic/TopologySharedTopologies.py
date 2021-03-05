import bpy
from bpy.props import StringProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import cppyy

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

def processItem(input):
    topoA = input[0]
    topoA.__class__ = Topology
    topoB = input[1]
    topoB.__class__ = Topology
    typeFilter = input[2]
    print([topoA, topoB, typeFilter])
    topologies = []
    stl_list = cppyy.gbl.std.list[Topology.Ptr]()
    _ = topoA.SharedTopologies(topoB, typeFilter, stl_list)
    for aTopology in stl_list:
        topologies.append(fixTopologyClass(aTopology))
    print(topologies)
    return topologies

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

class SvTopologySharedTopologies(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Topologic
    Tooltip: Returns the shared topologies of the two input toplogies of a certain type specified by the input typeFilter
    """
    bl_idname = 'SvTopologySharedTopologies'
    bl_label = 'Topology.SharedTopologies'
    TypeFilter: IntProperty(name="Type Filter", default=255, update=updateNode)
    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Topology A')
        self.inputs.new('SvStringsSocket', 'Topology B')
        self.inputs.new('SvStringsSocket', 'Type Filter').prop_name = 'TypeFilter'
        self.outputs.new('SvStringsSocket', 'Topologies')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        topologyAList = self.inputs['Topology A'].sv_get(deepcopy=False)[0]
        topologyBList = self.inputs['Topology B'].sv_get(deepcopy=False)[0]
        typeFilterList = self.inputs['Type Filter'].sv_get(deepcopy=False)[0]
        maxLength = max([len(topologyAList), len(topologyBList), len(typeFilterList)])
        for i in range(len(topologyAList), maxLength):
            topologyAList.append(topologyAList[-1])
        for i in range(len(topologyBList), maxLength):
            topologyBList.append(topologyBList[-1])
        for i in range(len(topologyBList), maxLength):
            typeFilterList.append(typeFilterList[-1])
        topologies = []
        if (len(topologyAList) == len(topologyBList)):
            topologies = zip(topologyAList, topologyBList, typeFilterList)
            resultList = []
            for aTopologyTuple in topologies:
                resultList.append(recur(aTopologyTuple))
            self.outputs['Topologies'].sv_set(resultList)

def register():
    bpy.utils.register_class(SvTopologySharedTopologies)

def unregister():
    bpy.utils.unregister_class(SvTopologySharedTopologies)
