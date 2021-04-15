import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy
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
	vertices = cppyy.gbl.std.list[Vertex.Ptr]()
	_ = cell.Vertices(vertices)
	x = []
	y = []
	z = []
	for aVertex in vertices:
		x.append(vertices.X())
		y.append(vertices.Y())
		z.append(vertices.Z())
	return ([min(x), min(y), min(z), max(x), max(y), max(z)])

def processItem(input):
	vertex = input[0]
	cells = input[1]
	exclusive = input[2]
	tolerance = input[3]
	usedCells = input[4]
	for i in range(len(cells)):
		if exclusive == True and usedCells[i] == 1:
			continue
		bbox = boundingBox(cells[i])
		minX = bbox[0]
		if ((vertex.X() < bbox[0]) or (vertex.Y() < bbox[1]) or (vertex.Z() < bbox[2]) or (vertex.X() > bbox[3]) or (vertex.Y() > bbox[4]) or (vertex.Z() > bbox[5])) == False:
			if topologic.CellUtility.Contains(cells[i], vertex, tolerance) == 0:
				return(cells[i], i)
	return [None, None]

class SvVertexEnclosingCell(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Finds the nearest vertex to the input Vertex within the list of input vertices
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
		usedCellsList = []
		for cells in cellsList:
			usedCells = []
			for cell in cells:
				usedCells.append(0)
			usedCellsList.append(usedCells)
		matchLengths([vertexList, cellsList, exclusiveList, toleranceList, usedCellsList])
		inputs = zip(vertexList, cellsList, exclusiveList, toleranceList, usedCellsList)
		for anInput in inputs:
			result = processItem(anInput)
			enclosingCell = result[0]
			if enclosingCell != None:
				index = result[1]
				anInput[4][index] = 1
			outputs.append(enclosingCell)
		end = time.time()
		print("Enclosing Cell Operation consumed "+str(round(end - start,4))+" seconds")
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvVertexEnclosingCell)

def unregister():
	bpy.utils.unregister_class(SvVertexEnclosingCell)
