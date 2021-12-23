import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import json

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(hbjson, filepath, overwrite):
	# Make sure the file extension is .BREP
	ext = filepath[len(filepath)-7:len(filepath)]
	if ext.lower() != ".hbjson":
		filepath = filepath+".hbjson"
	f = None
	try:
		if overwrite == True:
			f = open(filepath, "w")
		else:
			f = open(filepath, "x") # Try to create a new File
	except:
		raise Exception("Error: Could not create a new file at the following location: "+filepath)
	if (f):
		json.dump(hbjson[0], f, indent=4)
		f.close()	
		return True
	return False

class SvEnergyModelExportToHBJSON(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Exports the input HBJSON string to a file   
	"""
	bl_idname = 'SvEnergyModelExportToHBJSON'
	bl_label = 'EnergyModel.ExportToHBJSON'
	OverwriteProp: BoolProperty(name="Overwrite", default=True, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'HBJSON')
		self.inputs.new('SvStringsSocket', 'File Path')
		self.inputs.new('SvStringsSocket', 'Overwrite File').prop_name = 'OverwriteProp'
		self.outputs.new('SvStringsSocket', 'Status')

	def process(self):
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Status'].sv_set([False])
			return
		hbjsonList = self.inputs['HBJSON'].sv_get(deepcopy=False)
		filepath = self.inputs['File Path'].sv_get(deepcopy=False)[0][0] #accept only one file path 
		overwrite = self.inputs['Overwrite File'].sv_get(deepcopy=False)[0][0] #accept only one overwrite flag
		self.outputs['Status'].sv_set([processItem(hbjsonList, filepath, overwrite)])

def register():
	bpy.utils.register_class(SvEnergyModelExportToHBJSON)

def unregister():
	bpy.utils.unregister_class(SvEnergyModelExportToHBJSON)
