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
    sets = item.getDefaultScheduleSets()
    names = []
    for aSet in sets:
        names.append(aSet.name().get())
    return [sets, names]
		
class SvEnergyModelDefaultScheduleSets(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Returns the default Schedule Sets found in the input Energy Model
	"""
	bl_idname = 'SvEnergyModelDefaultScheduleSets'
	bl_label = 'EnergyModel.DefaultScheduleSets'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Energy Model')
		self.outputs.new('SvStringsSocket', 'Sets')
		self.outputs.new('SvStringsSocket', 'Names')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Sets'].sv_set([])
			self.outputs['Names'].sv_set([])
			return
		inputs = self.inputs['Energy Model'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		setOutputs = []
		nameOutputs = []
		for anInput in inputs:
			sets, names = processItem(anInput)
			setOutputs.append(sets)
			nameOutputs.append(names)
		self.outputs['Sets'].sv_set(setOutputs)
		self.outputs['Names'].sv_set(nameOutputs)

def register():
	bpy.utils.register_class(SvEnergyModelDefaultScheduleSets)

def unregister():
	bpy.utils.unregister_class(SvEnergyModelDefaultScheduleSets)
