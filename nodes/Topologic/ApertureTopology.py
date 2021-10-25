import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

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

def processItem(item):
	return topologic.Aperture.Topology(item)


class SvApertureTopology(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Topology of the input Aperture   
	"""
	bl_idname = 'SvApertureTopology'
	bl_label = 'Aperture.Topology'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Aperture')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		apertureList = self.inputs['Aperture'].sv_get(deepcopy=True)
		apertureList = flatten(apertureList)
		outputs = []
		for anAperture in apertureList:
			outputs.append(processItem(anAperture))
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvApertureTopology)

def unregister():
    bpy.utils.unregister_class(SvApertureTopology)
