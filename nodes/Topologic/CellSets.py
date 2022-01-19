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

def processItem(inputCells, superCells, tol):
	if len(superCells) == 0:
		cluster = inputCells[0]
		for i in range(1, len(inputCells)):
			oldCluster = cluster
			cluster = cluster.Union(inputCells[i])
			del oldCluster
		superCells = []
		_ = cluster.Cells(None, superCells)
	unused = []
	for i in range(len(inputCells)):
		unused.append(True)
	sets = []
	for i in range(len(superCells)):
		sets.append([])
	for i in range(len(inputCells)):
		if unused[i]:
			iv = topologic.CellUtility.InternalVertex(inputCells[i], tol)
			for j in range(len(superCells)):
				if (topologic.CellUtility.Contains(superCells[j], iv, tol) == 0):
					sets[j].append(inputCells[i])
					unused[i] = False
	return sets

class SvCellSets(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: bundles the input Cells into Sets
	"""
	bl_idname = 'SvCellSets'
	bl_label = 'Cell.Sets'
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Cells')
		self.inputs.new('SvStringsSocket', 'SuperCells')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Sets')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		cellList = self.inputs['Cells'].sv_get(deepcopy=False)
		cellList = flatten(cellList)
		if not (self.inputs['SuperCells'].is_linked):
			superCellList = []
		else:
			superCellList = self.inputs['SuperCells'].sv_get(deepcopy=True)
			superCellList = flatten(superCellList)
		tolerance = self.inputs['Tolerance'].sv_get(deepcopy=False)[0][0]
		sets = processItem(cellList, superCellList, tolerance)
		self.outputs['Sets'].sv_set(sets)
		end = time.time()
		print("Cell.Sets Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvCellSets)

def unregister():
    bpy.utils.unregister_class(SvCellSets)
