import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item, angTol):
	return topologic.WireUtility.RemoveCollinearEdges(item, angTol) #This is an angle Tolerance

class SvWireRemoveCollinearEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Removes any collinear edges from the input Wire    
	"""
	bl_idname = 'SvWireRemoveCollinearEdges'
	bl_label = 'Wire.RemoveCollinearEdges'
	AngTol: FloatProperty(name='AngTol', default=0.1, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.inputs.new('SvStringsSocket', 'Angular Tolerance').prop_name='AngTol'
		self.outputs.new('SvStringsSocket', 'Wire')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		wires = self.inputs['Wire'].sv_get(deepcopy=False)
		angTol = self.inputs['Angular Tolerance'].sv_get(deepcopy=False)[0]

		wires = flatten(wires)
		output = []
		for aWire in wires:
			output.append(processItem(aWire, angTol))
		self.outputs['Wire'].sv_set(output)

def register():
    bpy.utils.register_class(SvWireRemoveCollinearEdges)

def unregister():
    bpy.utils.unregister_class(SvWireRemoveCollinearEdges)
