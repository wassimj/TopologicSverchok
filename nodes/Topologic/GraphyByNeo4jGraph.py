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
	node_labels =  graph.schema.node_labels
    relationship_types = graph.schema.relationship_types
    node_matcher = NodeMatcher(graph)
    relationship_matcher = RelationshipMatcher(graph)
    vertices = []
    edges = []
	for node_label in node_labels:
		nodes = list(node_matcher.match(node_label))
	for node in nodes:
		#Assume they have X, Y, Z coordinates
		vertex = topologic.Vertex.ByCoordinates(node['X'], node['Y'], node['Z'])
		vertex_dict['node'] = node
		vertex_dict['vertex'] = vertex
		vertex_dicts.append(vertex_dict)
		keys = list(node.keys())
		values = []
		for key in keys:
			print("  ",key.upper(),":",node[key])
			values.append(node[key])
		dict = processKeysValues(keys, values)
		_ = vertex.SetDictionary(dict)
	for node in nodes:
		for relationship_type in relationship_types:
			relationships = list(relationship_matcher.match([node], r_type=relationship_type))
			for relationship in relationships:
				print("    ",relationship.start_node['name'], relationship_type, relationship.end_node['name'])
				sv = topologic.Vertex.ByCoordinates(relationship.start_node['X'], relationship.start_node['Y'], relationship.start_node['Z'])
				ev = topologic.Vertex.ByCoordinates(relationship.end_node['X'], relationship.end_node['Y'], relationship.end_node['Z'])
				edge = topologic.Edge.ByStartVertexEndVertex(sv, ev)
				if relationship.start_node['name']:
					sv_name = relationship.start_node['name']
				else:
					sv_name = 'None'
					print("Found None SV NAME")
				if relationship.end_node['name']:
					ev_name = relationship.end_node['name']
				else:
					ev_name = 'None'
					print("Found None EV NAME")
				dict = processKeysValues(["relationship_type", "from", "to"], [relationship_type, sv_name, ev_name])
				if dict:
					print(dict)
					_ = edge.SetDictionary(dict)
				edges.append(edge)

return topologic.Graph.ByVerticesEdges(vertices,edges)

class SvGraphByNeo4jGraph(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Graph from the input Neo4j Graph   
	"""
	bl_idname = 'SvGraphByNeo4jGraph'
	bl_label = 'Graph.ByNeo4jGraph'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Neo4j Graph')
		self.outputs.new('SvStringsSocket', 'Graph')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		neo4jGraphList = self.inputs['Neo4j Graph'].sv_get(deepcopy=True)
		neo4jGraphList = flatten(neo4jGraphList)
		outputs = []
		for anInput in neo4jGraphList:
			outputs.append(processItem(anInput))
		self.outputs['Graph'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvGraphByNeo4jGraph)

def unregister():
    bpy.utils.unregister_class(SvGraphByNeo4jGraph)
