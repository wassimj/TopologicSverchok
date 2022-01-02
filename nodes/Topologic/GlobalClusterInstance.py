import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import time

def processItem():
	return topologic.GlobalCluster.GetInstance()

class SvGlobalClusterInstance(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Get an Instance of the Global Cluster    
	"""
	bl_idname = 'SvGlobalClusterInstance'
	bl_label = 'GlobalCluster.Instance'

	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Global Cluster')

	def process(self):
		start = time.time()
		outputs.append(processItem())
		self.outputs['Global Cluster'].sv_set(outputs)
		end = time.time()
		print("GlobalCluster.Instance Operation consumed "+str(round(end - start,2))+" seconds")

def register():
	bpy.utils.register_class(SvGlobalClusterInstance)

def unregister():
	bpy.utils.unregister_class(SvGlobalClusterInstance)
