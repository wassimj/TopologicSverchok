import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import sys
try:
	import ifcopenshell
	import ifcopenshell.geom
except:
	raise Exception("Error: TopologyByImportedIFC: ifcopenshell is not present on your system. Install BlenderBIM or ifcopenshell to resolve.")
import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

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
			output.append(topologic.Topology.ByString(brepString))
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
		outputs = flatten(outputs)
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvTopologyByImportedIFC)

def unregister():
    bpy.utils.unregister_class(SvTopologyByImportedIFC)
