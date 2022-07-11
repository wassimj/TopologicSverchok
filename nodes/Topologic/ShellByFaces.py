import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import warnings

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
	faces, tol = item
	shell = topologic.Shell.ByFaces(faces, tol)
	if not shell:
		warnings.warn("Warning: Default Shell.ByFaces method failed. Attempting to Merge the Faces.", UserWarning)
		result = faces[0]
		remainder = faces[1:]
		cluster = topologic.Cluster.ByTopologies(remainder, False)
		result = result.Merge(cluster, False)
		if result.Type() != 16: #16 is the type of a Shell
			warnings.warn("Warning: Input Faces do not form a Shell", UserWarning)
			if result.Type() > 16:
				returnShells = []
				_ = result.Shells(None, returnShells)
				return returnShells
			else:
				return None
	else:
		return shell

class SvShellByFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Shell from the list of input Faces  
	"""
	bl_idname = 'SvShellByFaces'
	bl_label = 'Shell.ByFaces'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)
	Level: IntProperty(name='Level', default =1,min=1, update = updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Faces')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.inputs.new('SvStringsSocket', 'Level').prop_name='Level'
		self.outputs.new('SvStringsSocket', 'Shell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		faceList = self.inputs['Faces'].sv_get(deepcopy=False)
		tol = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)[0][0]
		level = flatten(self.inputs['Level'].sv_get(deepcopy=False, default= 1))
		if isinstance(level,list):
			level = int(level[0])
		faceList = list(list_level_iter(faceList,level))
		faceList = [flatten(t) for t in faceList]
		outputs = []
		for t in range(len(faceList)):
			outputs.append(processItem([faceList[t], tol]))
		self.outputs['Shell'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvShellByFaces)

def unregister():
    bpy.utils.unregister_class(SvShellByFaces)
