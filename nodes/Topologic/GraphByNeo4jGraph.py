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

def randomVertex(vertices, minDistance):
	print("Creating a Random Vertex!")
	flag = True
	while flag:
		x = random.uniform(0, 1000)
		y = random.uniform(0, 1000)
		z = random.uniform(0, 1000)
		v = topologic.Vertex.ByCoordinates(x, y, z)
		test = False
		if len(vertices) < 1:
			return v
		for vertex in vertices:
			d = topologic.VertexUtility.Distance(v, vertex)
			if d < minDistance:
				test = True
				break
		if test == False:
			return v
		else:
			continue

def processKeysValues(keys, values):
    if len(keys) != len(values):
        raise Exception("DictionaryByKeysValues - Keys and Values do not have the same length")
    stl_keys = []
    stl_values = []
    for i in range(len(keys)):
        if isinstance(keys[i], str):
            stl_keys.append(keys[i])
        else:
            stl_keys.append(str(keys[i]))
        if isinstance(values[i], list) and len(values[i]) == 1:
            value = values[i][0]
        else:
            value = values[i]
        if isinstance(value, bool):
            if value == False:
                stl_values.append(topologic.IntAttribute(0))
            else:
                stl_values.append(topologic.IntAttribute(1))
        elif isinstance(value, int):
            stl_values.append(topologic.IntAttribute(value))
        elif isinstance(value, float):
            stl_values.append(topologic.DoubleAttribute(value))
        elif isinstance(value, str):
            stl_values.append(topologic.StringAttribute(value))
        elif isinstance(value, sp.CartesianPoint):
            value = list(value)
            l = []
            for v in value:
                if isinstance(v, bool):
                    l.append(topologic.IntAttribute(v))
                elif isinstance(v, int):
                    l.append(topologic.IntAttribute(v))
                elif isinstance(v, float):
                    l.append(topologic.DoubleAttribute(v))
                elif isinstance(v, str):
                    l.append(topologic.StringAttribute(v))
            stl_values.append(topologic.ListAttribute(l))
        elif isinstance(value, list):
            l = []
            for v in value:
                if isinstance(v, bool):
                    l.append(topologic.IntAttribute(v))
                elif isinstance(v, int):
                    l.append(topologic.IntAttribute(v))
                elif isinstance(v, float):
                    l.append(topologic.DoubleAttribute(v))
                elif isinstance(v, str):
                    l.append(topologic.StringAttribute(v))
            stl_values.append(topologic.ListAttribute(l))
        else:
            raise Exception("Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
    myDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
    return myDict
			

def processItem(item):
	neo4jGraph = item
	node_labels =  neo4jGraph.schema.node_labels
	relationship_types = neo4jGraph.schema.relationship_types
	node_matcher = NodeMatcher(neo4jGraph)
	relationship_matcher = RelationshipMatcher(neo4jGraph)
	vertices = []
	edges = []
	nodes = []
	for node_label in node_labels:
		nodes = nodes + (list(node_matcher.match(node_label)))
	print(nodes)
	for node in nodes:
		#Check if they have X, Y, Z coordinates
		if ('x' in node.keys()) and ('y' in node.keys()) and ('z' in node.keys()) or ('X' in node.keys()) and ('Y' in node.keys()) and ('Z' in node.keys()):
			x = node['x']
			y = node['y']
			z = node['z']
			vertex = topologic.Vertex.ByCoordinates(x, y, z)
		else:
			vertex = randomVertex(vertices, 1)
		keys = list(node.keys())
		values = []
		for key in keys:
			values.append(node[key])
		d = processKeysValues(keys, values)
		_ = vertex.SetDictionary(d)
		vertices.append(vertex)
	for node in nodes:
		for relationship_type in relationship_types:
			relationships = list(relationship_matcher.match([node], r_type=relationship_type))
			for relationship in relationships:
				print("    ",relationship.start_node['name'], relationship_type, relationship.end_node['name'])
				print("Nodes Index:",nodes.index(relationship.start_node))
				sv = vertices[nodes.index(relationship.start_node)]
				ev = vertices[nodes.index(relationship.end_node)]
				edge = topologic.Edge.ByStartVertexEndVertex(sv, ev)
				if relationship.start_node['name']:
					sv_name = relationship.start_node['name']
				else:
					sv_name = 'None'
				if relationship.end_node['name']:
					ev_name = relationship.end_node['name']
				else:
					ev_name = 'None'
				d = processKeysValues(["relationship_type", "from", "to"], [relationship_type, sv_name, ev_name])
				if d:
					_ = edge.SetDictionary(d)
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
