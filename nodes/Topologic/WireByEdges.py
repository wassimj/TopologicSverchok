import bpy
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary

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
	wire = None
	for anEdge in item:
		if anEdge.Type() == 2:
			if wire == None:
				wire = anEdge
			else:
				try:
					wire = wire.Merge(anEdge)
				except:
					continue
	if wire.Type() != 4:
		raise Exception("Error: Could not create Wire. Please check input")
	return wire

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input[0], list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem(input)
	return output

class SvWireByEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Wire from the list of input Edges    
	"""
	bl_idname = 'SvWireByEdges'
	bl_label = 'Wire.ByEdges'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Wire')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		edgeList = self.inputs['Edges'].sv_get(deepcopy=False)
		wires = recur(edgeList)
		self.outputs['Wire'].sv_set(flatten(wires))

def register():
    bpy.utils.register_class(SvWireByEdges)

def unregister():
    bpy.utils.unregister_class(SvWireByEdges)
