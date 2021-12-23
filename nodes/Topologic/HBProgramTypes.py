import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import honeybee_energy.lib.programtypes as prog_type_lib

def processItem():
	progTypes = []
	progIdentifiers = list(prog_type_lib.PROGRAM_TYPES)
	for progIdentifier in progIdentifiers: 
		progTypes.append(prog_type_lib.program_type_by_identifier(progIdentifier))
	return [progTypes, progIdentifiers]

class SvHBProgramTypes(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the available HB program types
	"""
	bl_idname = 'SvHBProgramTypes'
	bl_label = 'HBProgramTypes'
	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Program Types')
		self.outputs.new('SvStringsSocket', 'Program Identifiers')


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		progTypes, progIdentifiers = processItem()
		self.outputs['Program Types'].sv_set(progTypes)
		self.outputs['Program Identifiers'].sv_set(progIdentifiers)

def register():
	bpy.utils.register_class(SvHBProgramTypes)

def unregister():
	bpy.utils.unregister_class(SvHBProgramTypes)
