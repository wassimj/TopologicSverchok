import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty
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

def list_level_iter(lst, level, _current_level: int= 1):
    """
    Iterate over all lists with given nesting
    With level 1 it will return the given list
    With level 2 it will iterate over all nested lists in the main one
    If a level does not have lists on that level it will return empty list
    _current_level - for internal use only
    """
    if _current_level < level:
        try:
            for nested_lst in lst:
                if not isinstance(nested_lst, list):
                    raise TypeError
                yield from list_level_iter(nested_lst, level, _current_level + 1)
        except TypeError:
            yield []
    else:
        yield lst

def processItem(vertices):
	if len(vertices) < 2:
		return None
	edge = topologic.EdgeUtility.ByVertices(vertices)
	return edge

class SvEdgeByVertices(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates an Edge from the input Vertices
	"""
	bl_idname = 'SvEdgeByVertices'
	bl_label = 'Edge.ByVertices'
	Level: IntProperty(name='Level', default =2,min=1, update = updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertices')
		self.inputs.new('SvStringsSocket', 'Level').prop_name='Level'
		self.outputs.new('SvStringsSocket', 'Edge')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Edge'].sv_set([])
			return
		vertexList = self.inputs['Vertices'].sv_get(deepcopy=False)
		level = flatten(self.inputs['Level'].sv_get(deepcopy=False, default= 2))
		if isinstance(level,list):
			level = int(level[0])
		vertexList = list(list_level_iter(vertexList,level))
		vertexList = [flatten(t) for t in vertexList]
		outputs = []
		for t in range(len(vertexList)):
			outputs.append(processItem(vertexList[t]))
		self.outputs['Edge'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvEdgeByVertices)

def unregister():
    bpy.utils.unregister_class(SvEdgeByVertices)
