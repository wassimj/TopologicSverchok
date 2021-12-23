import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import honeybee_energy.lib.constructionsets as constr_set_lib

def processItem():
	constrSets = []
	constrIdentifiers = list(constr_set_lib.CONSTRUCTION_SETS)
	for constrIdentifier in constrIdentifiers: 
		constrSets.append(constr_set_lib.construction_set_by_identifier(constrIdentifier))
	return [constrSets, constrIdentifiers]

class SvHBConstructionSets(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the available HB construction sets
	"""
	bl_idname = 'SvHBConstructionSets'
	bl_label = 'HB.ConstructionSets'
	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Construction Sets')
		self.outputs.new('SvStringsSocket', 'Construction Identifiers')


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		constrSets, constrIdentifiers = processItem()
		self.outputs['Construction Sets'].sv_set(constrSets)
		self.outputs['Construction Identifiers'].sv_set(constrIdentifiers)

def register():
	bpy.utils.register_class(SvHBConstructionSets)

def unregister():
	bpy.utils.unregister_class(SvHBConstructionSets)
