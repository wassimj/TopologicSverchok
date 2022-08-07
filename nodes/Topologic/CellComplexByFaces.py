import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import warnings
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
	assert isinstance(faces, list), "CellComplex.ByFaces - Error: Input is not a list"
	faces = [x for x in faces if isinstance(x, topologic.Face)]
	cellComplex = topologic.CellComplex.ByFaces(faces, tol, False)
	if not cellComplex:
		warnings.warn("Warning: Default CellComplex.ByFaces method failed. Attempting to Merge the Faces.", UserWarning)
		cellComplex = faces[0]
		for i in range(1,len(faces)):
			newCellComplex = None
			try:
				newCellComplex = cellComplex.Merge(faces[i], False)
			except:
				warnings.warn("Warning: Failed to merge Face #"+i+". Skipping.", UserWarning)
			if newCellComplex:
				cellComplex = newCellComplex
		if cellComplex.Type() != 64: #64 is the type of a CellComplex
			warnings.warn("Warning: Input Faces do not form a CellComplex", UserWarning)
			if cellComplex.Type() > 64:
				returnCellComplexes = []
				_ = cellComplex.CellComplexes(None, returnCellComplexes)
				return returnCellComplexes
			else:
				return None
	else:
		return cellComplex

class SvCellComplexByFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a CellComplex from the list of input Faces  
	"""
	bl_idname = 'SvCellComplexByFaces'
	bl_label = 'CellComplex.ByFaces'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)
	Level: IntProperty(name='Level', default =1,min=1, update = updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Faces')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.inputs.new('SvStringsSocket', 'Level').prop_name='Level'
		self.outputs.new('SvStringsSocket', 'CellComplex')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			self.outputs['CellComplex'].sv_set([])
			return
		faceList = self.inputs['Faces'].sv_get(deepcopy=True)
		level = flatten(self.inputs['Level'].sv_get(deepcopy=False, default= 1))
		tol = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)[0][0]
		if isinstance(level,list):
			level = int(level[0])
		faceList = list(list_level_iter(faceList,level))
		faceList = [flatten(t) for t in faceList]
		outputs = []
		for t in range(len(faceList)):
			outputs.append(processItem([faceList[t], tol]))
		self.outputs['CellComplex'].sv_set(outputs)
		end = time.time()
		print("CellComplex.ByFaces Operation consumed "+str(round(end - start,2)*1000)+" ms")

def register():
    bpy.utils.register_class(SvCellComplexByFaces)

def unregister():
    bpy.utils.unregister_class(SvCellComplexByFaces)
