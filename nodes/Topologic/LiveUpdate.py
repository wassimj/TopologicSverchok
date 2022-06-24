import bpy
from sverchok.node_tree import SverchCustomTreeNode

class SvTopologicLiveUpate(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Enables Live Updating in Blender  
	"""
	bl_idname = 'SvTopologicLiveUpdate'
	bl_label = 'Topologic.LiveUpdate'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Input')
		self.outputs.new('SvStringsSocket', 'Output')
        # remove all previous handlers
		for h in bpy.app.handlers.depsgraph_update_post:
			bpy.app.handlers.depsgraph_update_post.remove(h)
		bpy.app.handlers.depsgraph_update_post.append(self.process())

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputList = self.inputs['Input'].sv_get(deepcopy=True)
		self.outputs['Output'].sv_set(inputList)

def register():
    bpy.utils.register_class(SvTopologicLiveUpate)

def unregister():
    bpy.utils.unregister_class(SvTopologicLiveUpate)
