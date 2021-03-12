import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item, tol):
	print(item)
	cellComplex = None
	faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	for aFace in item:
		faces.push_back(aFace)
	cellComplex = topologic.CellComplex.ByFaces(faces, tol)
	return cellComplex

def recur(input, tol):
	output = []
	if input == None:
		return []
	if isinstance(input[0], list):
		for anItem in input:
			output.append(recur(anItem, tol))
	else:
		output = processItem(input, tol)
	return output

class SvCellComplexByFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a CellComplex from the list of input Faces  
	"""
	bl_idname = 'SvCellComplexByFaces'
	bl_label = 'CellComplex.ByFaces'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Faces')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'CellComplex')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Faces'].sv_get(deepcopy=False)
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0][0]
		cellComplexes = recur(inputs, tol)
		self.outputs['CellComplex'].sv_set(flatten(cellComplexes))

def register():
    bpy.utils.register_class(SvCellComplexByFaces)

def unregister():
    bpy.utils.unregister_class(SvCellComplexByFaces)
