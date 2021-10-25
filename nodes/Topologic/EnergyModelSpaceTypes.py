import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

try:
	import openstudio
except:
	raise Exception("Error: Could not import openstudio.")

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
    types = item.getSpaceTypes()
    names = []
    colors = []
    for aType in types:
        names.append(aType.name().get())
        red = aType.renderingColor().get().renderingRedValue()
        green = aType.renderingColor().get().renderingGreenValue()
        blue = aType.renderingColor().get().renderingBlueValue()
        colors.append([red,green,blue])
    return [types, names, colors]
		
class SvEnergyModelSpaceTypes(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Returns the Space Types, Names, and Colors found in the input Energy Model
	"""
	bl_idname = 'SvEnergyModelSpaceTypes'
	bl_label = 'EnergyModel.SpaceTypes'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Energy Model')
		self.outputs.new('SvStringsSocket', 'Types')
		self.outputs.new('SvStringsSocket', 'Names')
		self.outputs.new('SvStringsSocket', 'Colors')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Types'].sv_set([])
			self.outputs['Names'].sv_set([])
			self.outputs['Colors'].sv_set([])
			return
		inputs = self.inputs['Energy Model'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		typeOutputs = []
		nameOutputs = []
		colorOutputs = []
		for anInput in inputs:
			types, names, colors = processItem(anInput)
			typeOutputs.append(types)
			nameOutputs.append(names)
			colorOutputs.append(colors)
		self.outputs['Types'].sv_set(typeOutputs)
		self.outputs['Names'].sv_set(nameOutputs)
		self.outputs['Colors'].sv_set(colorOutputs)

def register():
	bpy.utils.register_class(SvEnergyModelSpaceTypes)

def unregister():
	bpy.utils.unregister_class(SvEnergyModelSpaceTypes)
