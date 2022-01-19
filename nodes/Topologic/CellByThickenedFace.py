import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

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
	face = item[0]
	thickness = abs(item[1])
	bothSides = item[2]
	reverse = item[3]
	tolerance = item[4]

	if reverse == True and bothSides == False:
		thickness = -thickness
	faceNormal = topologic.FaceUtility.NormalAtParameters(face, 0.5, 0.5)
	if bothSides:
		bottomFace = topologic.TopologyUtility.Translate(face, -faceNormal[0]*0.5*thickness, -faceNormal[1]*0.5*thickness, -faceNormal[2]*0.5*thickness)
		topFace = topologic.TopologyUtility.Translate(face, faceNormal[0]*0.5*thickness, faceNormal[1]*0.5*thickness, faceNormal[2]*0.5*thickness)
	else:
		bottomFace = face
		topFace = topologic.TopologyUtility.Translate(face, faceNormal[0]*thickness, faceNormal[1]*thickness, faceNormal[2]*thickness)

	cellFaces = [bottomFace, topFace]
	bottomEdges = []
	_ = bottomFace.Edges(None, bottomEdges)
	for bottomEdge in bottomEdges:
		topEdge = topologic.TopologyUtility.Translate(bottomEdge, faceNormal[0]*thickness, faceNormal[1]*thickness, faceNormal[2]*thickness)
		sideEdge1 = topologic.Edge.ByStartVertexEndVertex(bottomEdge.StartVertex(), topEdge.StartVertex())
		sideEdge2 = topologic.Edge.ByStartVertexEndVertex(bottomEdge.EndVertex(), topEdge.EndVertex())
		cellWire = topologic.Wire.ByEdges([bottomEdge, sideEdge1, topEdge, sideEdge2])
		cellFaces.append(topologic.Face.ByExternalBoundary(cellWire))
	return topologic.Cell.ByFaces(cellFaces, tolerance)

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

class SvCellByThickenedFace(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cell by thickening the input Face    
	"""
	bl_idname = 'SvCellByThickenedFace'
	bl_label = 'Cell.ByThickenedFace'
	Thickness: FloatProperty(name="Thickness", default=1, min=0.0001, precision=4, update=updateNode)
	BothSides: BoolProperty(name="BothSides", default=True, update=updateNode)
	Reverse: BoolProperty(name="Reverse", default=False, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'Thickness').prop_name = 'Thickness'
		self.inputs.new('SvStringsSocket', 'Both Sides').prop_name = 'BothSides'
		self.inputs.new('SvStringsSocket', 'Reverse').prop_name = 'Reverse'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		faceList = flatten(faceList)
		thicknessList = self.inputs['Thickness'].sv_get(deepcopy=False)
		thicknessList = flatten(thicknessList)
		bothSidesList = self.inputs['Both Sides'].sv_get(deepcopy=False)
		bothSidesList = flatten(bothSidesList)
		reverseList = self.inputs['Reverse'].sv_get(deepcopy=False)
		reverseList = flatten(reverseList)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=False)
		toleranceList = flatten(toleranceList)
		matchLengths([faceList, thicknessList, bothSidesList, reverseList, toleranceList])
		inputs = zip(faceList, thicknessList, bothSidesList, reverseList, toleranceList)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellByThickenedFace)

def unregister():
	bpy.utils.unregister_class(SvCellByThickenedFace)
