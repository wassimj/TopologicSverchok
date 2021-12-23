import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import honeybee_energy.lib.programtypes as prog_type_lib
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
	return prog_type_lib.program_type_by_identifier(item)

class SvHBProgramTypeByIdentifier(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the HB Program Type associated with the input Program Identifier
	"""
	bl_idname = 'SvHBProgramTypeByIdentifier'
	bl_label = 'HB.ProgramTypeByIdentifier'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Program Identifier')
		self.outputs.new('SvStringsSocket', 'Program Type')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		identifierList = self.inputs['Program Identifier'].sv_get(deepcopy=True)
		identifierList = flatten(identifierList)
		outputs = []
		for anInput in identifierList:
			outputs.append(processItem(anInput))
		self.outputs['Program Type'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvHBProgramTypeByIdentifier)

def unregister():
	bpy.utils.unregister_class(SvHBProgramTypeByIdentifier)
