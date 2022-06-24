import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
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

def processItem(item):
	face = topologic.Face.ByExternalBoundary(item)
	return face

def recur(input):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem))
	else:
		output = processItem(input)
	return output
	
class SvFaceByWire(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Face from the input planar closed Wire   
	"""
	bl_idname = 'SvFaceByWire'
	bl_label = 'Face.ByWire'
	Level: IntProperty(name='Level', default =2,min=1, update = updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.inputs.new('SvStringsSocket', 'Level').prop_name='Level'
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		wireList = self.inputs['Wire'].sv_get(deepcopy=True)
		level = flatten(self.inputs['Level'].sv_get(deepcopy=False, default= 2))
		if isinstance(level,list):
			level = int(level[0])
		wireList = list(list_level_iter(wireList,level))
		wireList = [flatten(t) for t in wireList]
		outputs = []s
		for t in range(len(wireList)):
			outputs.append(recur(wireList[t]))
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceByWire)

def unregister():
	bpy.utils.unregister_class(SvFaceByWire)
