import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import honeybee_energy.lib.constructionsets as constr_set_lib
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
	return constr_set_lib.construction_set_by_identifier(item)

class SvHBConstructionSetByIdentifier(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the HB Construction Set associated with the input Construction Set Identifier
	"""
	bl_idname = 'SvHBConstructionSetByIdentifier'
	bl_label = 'HB.ConstructionSetByIdentifier'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Construction Set Identifier')
		self.outputs.new('SvStringsSocket', 'Construction Set')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		identifierList = self.inputs['Construction Set Identifier'].sv_get(deepcopy=True)
		identifierList = flatten(identifierList)
		outputs = []
		for anInput in identifierList:
			outputs.append(processItem(anInput))
		self.outputs['Construction Set'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvHBConstructionSetByIdentifier)

def unregister():
	bpy.utils.unregister_class(SvHBConstructionSetByIdentifier)
