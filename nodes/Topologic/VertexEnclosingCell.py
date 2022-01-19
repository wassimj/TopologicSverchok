import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import time

def matchLengths(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

def boundingBox(cell):
	vertices = []
	_ = cell.Vertices(None, vertices)
	x = []
	y = []
	z = []
	for aVertex in vertices:
		x.append(aVertex.X())
		y.append(aVertex.Y())
		z.append(aVertex.Z())
	return ([min(x), min(y), min(z), max(x), max(y), max(z)])

def processItem(input):
	vertex = input[0]
	cells = input[1]
	exclusive = input[2]
	tolerance = input[3]
	enclosingCells = []
	for i in range(len(cells)):
		bbox = boundingBox(cells[i])
		minX = bbox[0]
		if ((vertex.X() < bbox[0]) or (vertex.Y() < bbox[1]) or (vertex.Z() < bbox[2]) or (vertex.X() > bbox[3]) or (vertex.Y() > bbox[4]) or (vertex.Z() > bbox[5])) == False:
			if topologic.CellUtility.Contains(cells[i], vertex, tolerance) == 0:
				if exclusive:
					return([cells[i]])
				else:
					enclosingCells.append(cells[i])
	return enclosingCells

class SvVertexEnclosingCell(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Cell that contains the input Vertex from the list of input Cells
	"""
	bl_idname = 'SvVertexEnclosingCell'
	bl_label = 'Vertex.EnclosingCell'
	Exclusive: BoolProperty(name="Exclusive", default=True, update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)


	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.inputs.new('SvStringsSocket', 'Cells')
		self.inputs.new('SvStringsSocket', 'Exclusive').prop_name = 'Exclusive'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		vertexList = self.inputs['Vertex'].sv_get(deepcopy=False)
		cellsList = self.inputs['Cells'].sv_get(deepcopy=False)
		exclusiveList = self.inputs['Exclusive'].sv_get(deepcopy=False)[0]
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=False)[0]

		if isinstance(cellsList[0], list) == False:
			cellsList = [cellsList]
		outputs = []
		matchLengths([vertexList, cellsList, exclusiveList, toleranceList])
		inputs = zip(vertexList, cellsList, exclusiveList, toleranceList)
		for anInput in inputs:
			outputs.append(processItem(anInput))
		end = time.time()
		print("Enclosing Cell Operation consumed "+str(round(end - start,4))+" seconds")
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvVertexEnclosingCell)

def unregister():
	bpy.utils.unregister_class(SvVertexEnclosingCell)
