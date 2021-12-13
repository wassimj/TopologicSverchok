import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
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

def gcClear(item):
	gc = topologic.GlobalCluster.GetInstance()
	subTopologies = []
	_ = gc.SubTopologies(subTopologies)
	for aSubTopology in subTopologies:
		if not (topologic.Topology.IsSame(item, aSubTopology)):
			gc.RemoveTopology(aSubTopology)
	return

def processItem(inputCells, tol):
	cluster = inputCells[0]
	start = time.time()
	for i in range(1, len(inputCells)):
		oldCluster = cluster
		cluster = cluster.Union(inputCells[i])
		del oldCluster
		if i % 50 == 0:
			end = time.time()
			print("Operation consumed "+str(round(end - start,2))+" seconds")
			start = time.time()
			print(i,"Clearing GlobalCluster")
			gcClear(cluster)
	superCells = []
	_ = cluster.Cells(superCells)
	return superCells

class SvCellSuperCells(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Returns the Super Cells representing detached bundles of the input Cells
	"""
	bl_idname = 'SvCellSuperCells'
	bl_label = 'Cell.SuperCells'
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cells')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'SuperCells')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		cellLists = self.inputs['Cells'].sv_get(deepcopy=False)
		tolerance = self.inputs['Tolerance'].sv_get(deepcopy=False)[0][0]
		outputs = []
		for aCellList in cellLists:
			outputs.append(processItem(aCellList, tolerance))
		self.outputs['SuperCells'].sv_set(outputs)
		end = time.time()
		print("Cell.SuperCells Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvCellSuperCells)

def unregister():
    bpy.utils.unregister_class(SvCellSuperCells)
