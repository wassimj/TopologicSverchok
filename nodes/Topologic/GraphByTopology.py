import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import cppyy
import time


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

def internalVertex(topology, tolerance):
	topology = fixTopologyClass(topology)
	vst = None
	classType = topology.GetType()
	if classType == 64: #CellComplex
		tempCells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		_ = topology.Cells(tempCells)
		tempCell = tempCells.front()
		vst = topologic.CellUtility.InternalVertex(tempCell, tolerance)
	elif classType == 32: #Cell
		vst = topologic.CellUtility.InternalVertex(topology, tolerance)
	elif classType == 16: #Shell
		tempFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = topology.Faces(tempFaces)
		tempFace = tempFaces.front()
		vst = topologic.FaceUtility.InternalVertex(tempFace, tolerance)
	elif classType == 8: #Face
		vst = topologic.FaceUtility.InternalVertex(topology, tolerance)
	elif classType == 4: #Wire
		if topology.IsClosed():
			internalBoundaries = cppyy.gbl.std.list[topologic.Wire.Ptr]()
			tempFace = topologic.Face.ByExternalInternalBoundaries(topology, internalBoundaries)
			vst = topologic.FaceUtility.InternalVertex(tempFace, tolerance)
		else:
			tempEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = topology.Edges(tempEdges)
			vst = topologic.EdgeUtility.PointAtParameter(tempVertex.front(), 0.5)
	elif classType == 2: #Edge
		vst = topologic.EdgeUtility.PointAtParameter(topology, 0.5)
	elif classType == 1: #Vertex
		vst = topology
	else:
		vst = topology.CenterOfMass()
	return vst

def processCellComplex(item):
	topology = item[0]
	direct = item[1]
	directApertures = item[2]
	viaSharedTopologies = item[3]
	viaSharedApertures = item[4]
	toExteriorTopologies = item[5]
	toExteriorApertures = item[6]
	useInternalVertex = item[7]
	tolerance = item[8]
	graph = None
	edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	cellmat = []
	if direct == True:
		cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		_ = topology.Cells(cells)
		cells = list(cells)
		# Create a matrix of zeroes
		for i in range(len(cells)):
			cellRow = []
			for j in range(len(cells)):
				cellRow.append(0)
			cellmat.append(cellRow)
		for i in range(len(cells)):
			for j in range(len(cells)):
				if (i != j) and cellmat[i][j] == 0:
					cellmat[i][j] = 1
					cellmat[j][i] = 1
					sharedt = cppyy.gbl.std.list[topologic.Topology.Ptr]()
					cells[i].SharedTopologies(cells[j], 8, sharedt)
					sharedt = list(sharedt)
					if len(sharedt) > 0:
						if useInternalVertex == True:
							v1 = topologic.CellUtility.InternalVertex(cells[i], tolerance)
							v2 = topologic.CellUtility.InternalVertex(cells[j], tolerance)
						else:
							v1 = cells[i].CenterOfMass()
							v2 = cells[j].CenterOfMass()
						e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
						edges.push_back(e)
	if directApertures == True:
		cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		_ = topology.Cells(cells)
		cells = list(cells)
		# Create a matrix of zeroes
		for i in range(len(cells)):
			cellRow = []
			for j in range(len(cells)):
				cellRow.append(0)
			cellmat.append(cellRow)
		for i in range(len(cells)):
			for j in range(len(cells)):
				if (i != j) and cellmat[i][j] == 0:
					cellmat[i][j] = 1
					cellmat[j][i] = 1
					sharedt = cppyy.gbl.std.list[topologic.Topology.Ptr]()
					cells[i].SharedTopologies(cells[j], 8, sharedt)
					sharedt = list(sharedt)
					if len(sharedt) > 0:
						apertureExists = False
						for x in sharedt:
							ap = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
							_ = x.Apertures(ap)
							if len(ap) > 0:
								apertureExists = True
								break
						if apertureExists:
							if useInternalVertex == True:
								v1 = topologic.CellUtility.InternalVertex(cells[i], tolerance)
								v2 = topologic.CellUtility.InternalVertex(cells[j], tolerance)
							else:
								v1 = cells[i].CenterOfMass()
								v2 = cells[j].CenterOfMass()
							e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
							edges.push_back(e)

	cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
	_ = topology.Cells(cells)
	if (viaSharedTopologies == True) or (viaSharedApertures == True) or (toExteriorTopologies == True) or (toExteriorApertures == True):
		for aCell in cells:
			if useInternalVertex == True:
				vCell = topologic.CellUtility.InternalVertex(aCell, tolerance)
			else:
				vCell = aCell.CenterOfMass()
			vertices.push_back(vCell)
			faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
			_ = aCell.Faces(faces)
			sharedTopologies = []
			exteriorTopologies = []
			sharedApertures = []
			exteriorApertures = []
			for aFace in faces:
				cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
				_ = aFace.Cells(cells)
				cells = list(cells)
				if len(cells) > 1:
					sharedTopologies.append(aFace)
					apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
					_ = aFace.Apertures(apertures)
					for anAperture in apertures:
						sharedApertures.append(anAperture)
				else:
					exteriorTopologies.append(aFace)
					apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
					_ = aFace.Apertures(apertures)
					for anAperture in apertures:
						exteriorApertures.append(anAperture)
			if viaSharedTopologies:
				for sharedTopology in sharedTopologies:
					if useInternalVertex == True:
						vst = internalVertex(sharedTopology, tolerance)
					else:
						vst = sharedTopology.CenterOfMass()
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))
			if viaSharedApertures:
				for sharedAperture in sharedApertures:
					if useInternalVertex == True:
						vst = internalVertex(sharedAperture.Topology(), tolerance)
					else:
						vst = sharedAperture.Topology().CenterOfMass()
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))
			if toExteriorTopologies:
				for exteriorTopology in exteriorTopologies:
					if useInternalVertex == True:
						vst = internalVertex(exteriorTopology, tolerance)
					else:
						vst = exteriorTopology.CenterOfMass()
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))
			if toExteriorApertures:
				for exteriorAperture in exteriorApertures:
					extTop = exteriorAperture.Topology()
					if useInternalVertex == True:
						vst = internalVertex(extTop, tolerance)
					else:
						vst = exteriorAperture.Topology().CenterOfMass()
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))

	for aCell in cells:
		if useInternalVertex == True:
			vCell = internalVertex(aCell, tolerance)
		else:
			vCell = aCell.CenterOfMass()
		vertices.push_back(vCell)
	finalTopologies = cppyy.gbl.std.list[topologic.Topology.Ptr]()
	if len(list(edges)) > 0:
		for e in edges:
			finalTopologies.push_back(e)
	if len(list(vertices)) > 0:
		for v in vertices:
			finalTopologies.push_back(v)
		cluster = topologic.Cluster.ByTopologies(finalTopologies)
		cluster = cluster.SelfMerge()
		graph = topologic.Graph.ByTopology(cluster, True, False, False, False, False, False, tolerance)
		return graph
	elif len(list(vertices)) > 0:
		for v in vertices:
			finalTopologies.push_back(v)
		cluster = topologic.Cluster.ByTopologies(finalTopologies)
		graph = topologic.Graph.ByTopology(cluster, True, False, False, False, False, False, tolerance)
		return graph
	return None

def processCell(item):
	cell = item[0]
	toExteriorTopologies = item[5]
	toExteriorApertures = item[6]
	useInternalVertex = item[7]
	tolerance = item[8]
	graph = None
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()

	if useInternalVertex == True:
		vCell = topologic.CellUtility.InternalVertex(cell, tolerance)
	else:
		vCell = cell.CenterOfMass()

	if (toExteriorTopologies == True) or (toExteriorApertures == True):
		vertices.push_back(vCell)
		faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = cell.Faces(faces)
		exteriorTopologies = []
		exteriorApertures = []
		for aFace in faces:
			exteriorTopologies.append(aFace)
			apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
			_ = aFace.Apertures(apertures)
			for anAperture in apertures:
				exteriorApertures.append(anAperture)
			if toExteriorTopologies:
				for exteriorTopology in exteriorTopologies:
					if useInternalVertex == True:
						vst = internalVertex(exteriorTopology, tolerance)
					else:
						vst = exteriorTopology.CenterOfMass()
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))
			if toExteriorApertures:
				for exteriorAperture in exteriorApertures:
					extTop = exteriorAperture.Topology()
					if useInternalVertex == True:
						vst = internalVertex(extTop, tolerance)
					else:
						vst = exteriorAperture.Topology().CenterOfMass()
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))
	else:
		vertices.push_back(vCell)

	finalTopologies = cppyy.gbl.std.list[topologic.Topology.Ptr]()
	if len(list(edges)) > 0:
		for e in edges:
			finalTopologies.push_back(e)
		cluster = topologic.Cluster.ByTopologies(finalTopologies)
		cluster = cluster.SelfMerge()
		graph = topologic.Graph.ByTopology(cluster, True, False, False, False, False, False, tolerance)
		return graph
	else:
		graph = topologic.Graph.ByTopology(vCell, True, False, False, False, False, False, tolerance)
		return graph
	return None

def processItem(item):
	topology = item[0]
	classType = topology.GetType()
	graph = None
	if classType == 64: #CellComplex
		graph = processCellComplex(item)
	elif classType == 32: #Cell
		graph = processCell(item)
	return graph

class SvGraphByTopology(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Dual Graph of the input Topology
	"""
	bl_idname = 'SvGraphByTopology'
	bl_label = 'Graph.ByTopology'
	DirectProp: BoolProperty(name="Direct", default=True, update=updateNode)
	DirectIfSharedAperturesProp: BoolProperty(name="Direct If Shared Apertures", default=False, update=updateNode)
	ViaSharedTopologiesProp: BoolProperty(name="Via Shared Topologies", default=False, update=updateNode)
	ViaSharedAperturesProp: BoolProperty(name="Via Shared Apertures", default=False, update=updateNode)
	ToExteriorTopologiesProp: BoolProperty(name="To Exterior Topoloogies", default=False, update=updateNode)
	ToExteriorAperturesProp: BoolProperty(name="To Exterior Apertures", default=False, update=updateNode)
	UseInternalVertexProp: BoolProperty(name="Use Internal Vertex", default=False, update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Direct').prop_name = 'DirectProp'
		self.inputs.new('SvStringsSocket', 'DirectIfSharedApertures').prop_name = 'DirectIfSharedAperturesProp'
		self.inputs.new('SvStringsSocket', 'ViaSharedTopologies').prop_name = 'ViaSharedTopologiesProp'
		self.inputs.new('SvStringsSocket', 'ViaSharedApertures').prop_name = 'ViaSharedAperturesProp'
		self.inputs.new('SvStringsSocket', 'ToExteriorTopologies').prop_name = 'ToExteriorTopologiesProp'
		self.inputs.new('SvStringsSocket', 'ToExteriorApertures').prop_name = 'ToExteriorAperturesProp'
		self.inputs.new('SvStringsSocket', 'UseInternalVertex').prop_name = 'UseInternalVertexProp'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Graph')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Graph'].sv_set([])
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		directList = self.inputs['Direct'].sv_get(deepcopy=False)[0]
		directAperturesList = self.inputs['DirectIfSharedApertures'].sv_get(deepcopy=False)[0]
		viaSharedTopologiesList = self.inputs['ViaSharedTopologies'].sv_get(deepcopy=False)[0]
		viaSharedAperturesList = self.inputs['ViaSharedApertures'].sv_get(deepcopy=False)[0]
		toExteriorTopologiesList = self.inputs['ToExteriorTopologies'].sv_get(deepcopy=False)[0]
		toExteriorAperturesList = self.inputs['ToExteriorApertures'].sv_get(deepcopy=False)[0]
		useInternalVertexList = self.inputs['UseInternalVertex'].sv_get(deepcopy=False)[0]
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=False)[0]

		maxLength = max([len(topologyList), len(directList), len(directAperturesList), len(viaSharedTopologiesList), len(viaSharedAperturesList), len(toExteriorTopologiesList), len(toExteriorAperturesList), len(useInternalVertexList), len(toleranceList)])
		for i in range(len(topologyList), maxLength):
			topologyList.append(topologyList[-1])

		for i in range(len(directList), maxLength):
			directList.append(directList[-1])

		for i in range(len(directAperturesList), maxLength):
			directAperturesList.append(directAperturesList[-1])

		for i in range(len(viaSharedTopologiesList), maxLength):
			viaSharedTopologiesList.append(viaSharedTopologiesList[-1])

		for i in range(len(viaSharedAperturesList), maxLength):
			viaSharedAperturesList.append(viaSharedAperturesList[-1])

		for i in range(len(toExteriorTopologiesList), maxLength):
			toExteriorTopologiesList.append(toExteriorTopologiesList[-1])

		for i in range(len(toExteriorAperturesList), maxLength):
			toExteriorAperturesList.append(toExteriorAperturesList[-1])

		for i in range(len(useInternalVertexList), maxLength):
			useInternalVertexList.append(useInternalVertexList[-1])

		for i in range(len(toleranceList), maxLength):
			toleranceList.append(toleranceList[-1])

		inputs = []
		outputs = []
		if (len(topologyList) == len(directList) == len(directAperturesList) == len(viaSharedTopologiesList) == len(viaSharedAperturesList) == len(toExteriorTopologiesList) == len(toExteriorAperturesList) == len(useInternalVertexList) == len(toleranceList)):
			inputs = zip(topologyList, directList, directAperturesList, viaSharedTopologiesList, viaSharedAperturesList, toExteriorTopologiesList, toExteriorAperturesList, useInternalVertexList, toleranceList)
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Graph'].sv_set(outputs)
		end = time.time()
		print("Graph.ByTopology Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphByTopology)

def unregister():
    bpy.utils.unregister_class(SvGraphByTopology)
