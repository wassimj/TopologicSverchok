import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.core.update_system import make_tree_from_nodes, do_update
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
import time


class SvExecuteRun(bpy.types.Operator, SvGenericNodeLocator):

	bl_idname = "topologic.run"
	bl_label = "Run"
	def sv_execute(self, context, node):
		#node.do_run = True
		node.outputs['Status'].sv_set([True])
		tree = node.id_data
		update_list = make_tree_from_nodes([node.name], tree)
		do_update(update_list, tree.nodes)
		#time.sleep(4)
		#node.outputs['Status'].sv_set([False])
		#update_list = make_tree_from_nodes([node.name], tree)
		#do_update(update_list, tree.nodes)

class SvExecuteReset(bpy.types.Operator, SvGenericNodeLocator):

	bl_idname = "topologic.reset"
	bl_label = "Reset"
	def sv_execute(self, context, node):
		#node.do_run = True
		node.outputs['Status'].sv_set([False])
		tree = node.id_data
		update_list = make_tree_from_nodes([node.name], tree)
		do_update(update_list, tree.nodes)
		#time.sleep(4)
		#node.outputs['Status'].sv_set([False])
		#update_list = make_tree_from_nodes([node.name], tree)
		#do_update(update_list, tree.nodes)
	
		
class SvTopologicRun(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True when Run button is pressed then outputs False
	"""
	bl_idname = 'SvTopologicRun'
	bl_label = 'Topology.Run'

	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Status')
	def draw_buttons(self, context, layout):
		row = layout.row(align=True)
		row.scale_y = 2
		self.wrapper_tracked_ui_draw_op(row, "topologic.reset", icon='CANCEL', text="RESET")
		row = layout.row(align=True)
		row.scale_y = 2
		self.wrapper_tracked_ui_draw_op(row, "topologic.run", icon='PLAY', text="RUN")

def register():
	bpy.utils.register_class(SvTopologicRun)
	bpy.utils.register_class(SvExecuteRun)
	bpy.utils.register_class(SvExecuteReset)


def unregister():
	bpy.utils.unregister_class(SvTopologicRun)
	bpy.utils.unregister_class(SvExecuteRun)
	bpy.utils.unregister_class(SvExecuteReset)
