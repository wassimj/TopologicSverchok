import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import sys
sys.path.append("C:\\ProgramData\\Anaconda3\\envs\\Blender377\\Lib\\site-packages")
import ifcopenshell
import ifcopenshell.geom
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

def classByType(argument):
	switcher = {
		1: Vertex,
		2: Edge,
		4: Wire,
		8: Face,
		16: Shell,
		32: Cell,
		64: CellComplex,
		128: Cluster }
	return switcher.get(argument, Topology)

def fixTopologyClass(topology):
	topology.__class__ = classByType(topology.GetType())
	return topology

def processItem(item):
	settings = ifcopenshell.geom.settings()
	settings.set(settings.USE_BREP_DATA,True)
	settings.set(settings.SEW_SHELLS,True)
	settings.set(settings.USE_WORLD_COORDS,True)

	ifc_file = ifcopenshell.open(item)
	products = ifc_file.by_type('IfcProduct')
	output = []
	for p in products:
		try:
			cr = ifcopenshell.geom.create_shape(settings, p)
			brepString = cr.geometry.brep_data
			output.append(fixTopologyClass(topologic.Topology.ByString(brepString)))
		except:
			continue
	return output

class SvTopologyByImportedIFC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology from the input IFC file 
	"""
	bl_idname = 'SvTopologyByImportedIFC'
	bl_label = 'Topology.ByImportedIFC'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'File Path')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['File Path'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvTopologyByImportedIFC)

def unregister():
    bpy.utils.unregister_class(SvTopologyByImportedIFC)
