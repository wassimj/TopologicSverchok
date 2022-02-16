import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic
import time
import random
from py2neo.data import spatial as sp

try:
	import py2neo
	from py2neo import Node,Relationship,Graph,Path,Subgraph
	from py2neo import NodeMatcher,RelationshipMatcher
except:
	raise Exception("Error: Could not import py2neo.")

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
	neo4jGraph = item
	return neo4jGraph.schema.node_labels

class SvNeo4jGraphNodeLabels(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Graph from the input Neo4j Graph   
	"""
	bl_idname = 'SvNeo4jGraphNodeLabels'
	bl_label = 'Neo4jGraph.NodeLabels'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Neo4j Graph')
		self.outputs.new('SvStringsSocket', 'Node Labels')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		neo4jGraphList = self.inputs['Neo4j Graph'].sv_get(deepcopy=True)
		neo4jGraphList = flatten(neo4jGraphList)
		outputs = []
		for anInput in neo4jGraphList:
			outputs.append(processItem(anInput))
		self.outputs['Node Labels'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvNeo4jGraphNodeLabels)

def unregister():
    bpy.utils.unregister_class(SvNeo4jGraphNodeLabels)
