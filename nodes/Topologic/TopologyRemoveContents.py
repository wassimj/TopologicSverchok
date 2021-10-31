import bpy
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

def nest_level(obj):

    # Not a list? So the nest level will always be 0:
    if type(obj) != list:
        return 0

    # Now we're dealing only with list objects:

    max_level = 0
    for item in obj:
        # Getting recursively the level for each item in the list,
        # then updating the max found level:
        max_level = max(max_level, nest_level(item))

    # Adding 1, because 'obj' is a list (here is the recursion magic):
    return max_level + 1

class SvTopologyRemoveContents(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Removes the input Topology contents from the input Topology    
	"""
	bl_idname = 'SvTopologyRemoveContents'
	bl_label = 'Topology.RemoveContents'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Contents')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		contentListOfLists = self.inputs['Contents'].sv_get(deepcopy=False)
		if nest_level(contentListOfLists) == 2:
			contentListOfLists = [contentListOfLists]
		if len(topologyList) != len(contentListOfLists):
			return
		output = []
		for i in range(len(topologyList)):
			if isinstance(topologyList[i], list) == False:
				topologyList[i] = [topologyList[i]]
			contentList = contentListOfLists[i]
			contents = []
			for aContent in contentList:
				if isinstance(aContent, list) == False:
					aContent = [aContent]
				contents.append(aContent[0])
			newTopology = topologyList[i][0].RemoveContents(contents)
			newTopology.__class__ = topologyList[i][0].__class__
			output.append([newTopology])
		self.outputs['Topology'].sv_set(output)

def register():
    bpy.utils.register_class(SvTopologyRemoveContents)

def unregister():
    bpy.utils.unregister_class(SvTopologyRemoveContents)
