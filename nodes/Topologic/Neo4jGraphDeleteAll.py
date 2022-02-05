import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic
import time
try:
	import py2neo
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
	neo4jGraph.delete_all()
	return neo4jGraph

class SvNeo4jGraphDeleteAll(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Deletes all Nodes and Edges in the input Neo4j Graph   
	"""
	bl_idname = 'SvNeo4jGraphDeleteAll'
	bl_label = 'Neo4jGraph.DeleteAll'

	def sv_init(self, context):
		#self.inputs[0].label = 'Auto'
		self.inputs.new('SvStringsSocket', 'Neo4j Graph')
		self.inputs.new('SvStringsSocket', 'Wait For')
		self.outputs.new('SvStringsSocket', 'Neo4j Graph')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		neo4jGraphList = self.inputs['Neo4j Graph'].sv_get(deepcopy=True)
		if not (self.inputs['Wait For'].is_linked):
			waitForList = []
		else:
			waitForList = self.inputs['Wait For'].sv_get(deepcopy=True)
		neo4jGraphList = flatten(neo4jGraphList)
		outputs = []
		for anInput in neo4jGraphList:
			outputs.append(processItem(anInput))
		self.outputs['Neo4j Graph'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvNeo4jGraphDeleteAll)

def unregister():
    bpy.utils.unregister_class(SvNeo4jGraphDeleteAll)
