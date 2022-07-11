import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time

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
	return topologic.Cluster.ByTopologies(item, False)


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

class SvClusterByTopologies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cluster from the list of input Topologies  
	"""
	bl_idname = 'SvClusterByTopologies'
	bl_label = 'Cluster.ByTopologies'
	Level: IntProperty(name='Level', default =1,min=1, update = updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topologies')
		self.inputs.new('SvStringsSocket', 'Level').prop_name='Level'
		self.outputs.new('SvStringsSocket', 'Cluster')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = self.inputs['Topologies'].sv_get(deepcopy=False)
		level = flatten(self.inputs['Level'].sv_get(deepcopy=False, default= 1))
		if isinstance(level,list):
			level = int(level[0])
		topologyList = list(list_level_iter(topologyList,level))
		topologyList = [flatten(t) for t in topologyList]
		outputs = []
		for t in range(len(topologyList)):
			outputs.append(processItem(topologyList[t]))
		#outputs.append(processItem(topologyList))
		self.outputs['Cluster'].sv_set(outputs)
		end = time.time()
		print("Cluster.ByTopologies Operation consumed "+str(round(end - start,2)*1000)+" ms")

def register():
    bpy.utils.register_class(SvClusterByTopologies)

def unregister():
    bpy.utils.unregister_class(SvClusterByTopologies)
