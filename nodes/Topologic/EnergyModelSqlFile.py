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
    return item.sqlFile().get()
		
class SvEnergyModelSqlFile(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Returns the SQL file found in the input Energy Model
	"""
	bl_idname = 'SvEnergyModelSqlFile'
	bl_label = 'EnergyModel.SqlFile'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Energy Model')
		self.outputs.new('SvStringsSocket', 'Sql File')


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Sql File'].sv_set([])
			return
		inputs = self.inputs['Energy Model'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Sql File'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEnergyModelSqlFile)

def unregister():
	bpy.utils.unregister_class(SvEnergyModelSqlFile)
