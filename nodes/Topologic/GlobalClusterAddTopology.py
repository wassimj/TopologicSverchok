import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import time

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	gc = topologic.GlobalCluster.GetInstance()
	gc.AddTopology(item)
	return item

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvGlobalClusterAddTopology(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Adds the input Topology to the Global Cluster    
	"""
	bl_idname = 'SvGlobalClusterAddTopology'
	bl_label = 'GlobalCluster.AddTopology'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		start = time.time()
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		topologyList = flatten(topologyList)
		outputs = []
		for anInput in topologyList:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)
		end = time.time()
		print("GlobalCluster.AddTopology Operation consumed "+str(round(end - start,2))+" seconds")

def register():
	bpy.utils.register_class(SvGlobalClusterAddTopology)

def unregister():
	bpy.utils.unregister_class(SvGlobalClusterAddTopology)
