import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import cppyy

def classByType(argument):
	switcher = {
		1: Vertex,
		2: Edge,
		4: Wire,
		8: Face,
		16: Shell,
		32: Cell,
		64: CellComplex,
		128: Cluster }
	return switcher.get(argument, Topology)

def fixTopologyClass(topology):
  topology.__class__ = classByType(topology.GetType())
  return topology

def processItem(item):
	face = item[0]
	thickness = abs(item[1])
	bothSides = item[2]
	reverse = item[3]
	tolerance = item[4]

	if reverse == True and bothSides == False:
		thickness = -thickness
	print(face)
	faceNormal = topologic.FaceUtility.NormalAtParameters(face, 0.5, 0.5)
	if bothSides:
		bottomFace = fixTopologyClass(topologic.TopologyUtility.Translate(face, -faceNormal.X()*0.5*thickness, -faceNormal.Y()*0.5*thickness, -faceNormal.Z()*0.5*thickness))
		topFace = fixTopologyClass(topologic.TopologyUtility.Translate(face, faceNormal.X()*0.5*thickness, faceNormal.Y()*0.5*thickness, faceNormal.Z()*0.5*thickness))
	else:
		bottomFace = face
		topFace = fixTopologyClass(topologic.TopologyUtility.Translate(face, faceNormal.X()*thickness, faceNormal.Y()*thickness, faceNormal.Z()*thickness))

	cellFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	cellFaces.push_back(bottomFace)
	cellFaces.push_back(topFace)
	bottomEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	_ = bottomFace.Edges(bottomEdges)
	for bottomEdge in bottomEdges:
		topEdge = fixTopologyClass(topologic.TopologyUtility.Translate(bottomEdge, faceNormal.X()*thickness, faceNormal.Y()*thickness, faceNormal.Z()*thickness))
		sideEdge1 = topologic.Edge.ByStartVertexEndVertex(bottomEdge.StartVertex(), topEdge.StartVertex())
		sideEdge2 = topologic.Edge.ByStartVertexEndVertex(bottomEdge.EndVertex(), topEdge.EndVertex())
		stlEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		stlEdges.push_back(bottomEdge)
		stlEdges.push_back(sideEdge1)
		stlEdges.push_back(topEdge)
		stlEdges.push_back(sideEdge2)
		cellWire = topologic.Wire.ByEdges(stlEdges)
		internalBoundaries = cppyy.gbl.std.list[topologic.Wire.Ptr]()
		cellFaces.push_back(topologic.Face.ByExternalInternalBoundaries(cellWire, internalBoundaries))
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
		thicknessList = self.inputs['Thickness'].sv_get(deepcopy=False)[0]
		bothSidesList = self.inputs['Both Sides'].sv_get(deepcopy=False)[0]
		reverseList = self.inputs['Reverse'].sv_get(deepcopy=False)[0]
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=False)[0]
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
