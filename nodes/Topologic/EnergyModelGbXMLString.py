import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from os.path import exists
try:
	import openstudio
except:
	raise Exception("Error: Could not import openstudio.")
import os

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
	return openstudio.gbxml.GbXMLForwardTranslator().modelToGbXMLString(item)

class SvEnergyModelGbXMLString(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Exports the input Energy Model to a gbXML file   
	"""
	bl_idname = 'SvEnergyModelGbXMLString'
	bl_label = 'EnergyModel.GbXMLString'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Energy Model')
		self.outputs.new('SvStringsSocket', 'GbXML')

	def process(self):
		modelList = self.inputs['Energy Model'].sv_get(deepcopy=True)
		modelList = flatten(modelList)
		inputs = modelList
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['GbXML'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEnergyModelGbXMLString)

def unregister():
	bpy.utils.unregister_class(SvEnergyModelGbXMLString)
