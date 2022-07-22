import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
#from sverchok.core.update_system import make_tree_from_nodes, do_update
from sverchok.core.update_system import UpdateTree
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.core.update_system import SearchTree
import time


class SvExecuteRun(bpy.types.Operator, SvGenericNodeLocator):

	bl_idname = "topologic.run"
	bl_label = "Run"
	def sv_execute(self, context, node):
		output = True
		if not (node.inputs['Input'].is_linked):
			output = [True]
		else:
			output = node.inputs['Input'].sv_get(deepcopy=False)[0]
		node.outputs['Output'].sv_set(output)
		tree = node.id_data
		stree = UpdateTree.get(tree)
		nodes = stree.nodes_from([node])
		tree.update_nodes(nodes)
		
class SvTopologicRun(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True when Run button is pressed then outputs False
	"""
	bl_idname = 'SvTopologicRun'
	bl_label = 'Topologic.Run'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Input')
		self.outputs.new('SvStringsSocket', 'Output')

	def draw_buttons(self, context, layout):
		row = layout.row(align=True)
		row.scale_y = 2
		self.wrapper_tracked_ui_draw_op(row, "topologic.run", icon='PLAY', text="RUN")

	def process(self):
		pass


def register():
	bpy.utils.register_class(SvTopologicRun)
	bpy.utils.register_class(SvExecuteRun)


def unregister():
	bpy.utils.unregister_class(SvTopologicRun)
	bpy.utils.unregister_class(SvExecuteRun)
