import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import cppyy
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

def repeat(list):
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

# From https://stackoverflow.com/questions/34432056/repeat-elements-of-list-between-each-other-until-we-reach-a-certain-length
def onestep(cur,y,base):
    # one step of the iteration
    if cur is not None:
        y.append(cur)
        base.append(cur)
    else:
        y.append(base[0])  # append is simplest, for now
        base = base[1:]+[base[0]]  # rotate
    return base

def iterate(list):
	maxLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		for i in range(len(anItem), maxLength):
			anItem.append(None)
		y=[]
		base=[]
		for cur in anItem:
			base = onestep(cur,y,base)
		returnList.append(y)
	return returnList

def trim(list):
	minLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength < minLength:
			minLength = newLength
	for anItem in list:
		anItem = anItem[:minLength]
		returnList.append(anItem)
	return returnList

# Adapted from https://stackoverflow.com/questions/533905/get-the-cartesian-product-of-a-series-of-lists
def interlace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in interlace(ar_list[1:]):
                yield [a,]+prod

def transposeList(l):
	length = len(l[0])
	returnList = []
	for i in range(length):
		tempRow = []
		for j in range(len(l)):
			tempRow.append(l[j][i])
		returnList.append(tempRow)
	return returnList


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

def relevantSelector(topology):
	returnVertex = None
	if topology.GetType() == topologic.Vertex.Type():
		return topology
	elif topology.GetType() == topologic.Edge.Type():
		return topologic.EdgeUtility.PointAtParameter(topology, 0.5)
	elif topology.GetType() == topologic.Face.Type():
		return topologic.FaceUtility.InternalVertex(topology)
	elif topology.GetType() == topologic.Cell.Type():
		return topologic.CellUtility.InternalVertex(topology)
	else:
		return topology.CenterOfMass()

def topologyContains(topology, vertex, tol):
	contains = False
	if topology.GetType() == topologic.Vertex.Type():
		try:
			contains = (topologic.VertexUtility.Distance(topology, vertex) <= tol)
		except:
			contains = False
		return contains
	elif topology.GetType() == topologic.Edge.Type():
		try:
			_ = topologic.EdgeUtility.ParameterAtPoint(topology, vertex)
			contains = True
		except:
			contains = False
		return contains
	elif topology.GetType() == topologic.Face.Type():
		return topologic.FaceUtility.IsInside(topology, vertex, tol)
	elif topology.GetType() == topologic.Cell.Type():
		return (topologic.CellUtility.Contains(topology, vertex, tol) == 0)
	return False

def getKeys(item):
	stlKeys = item.Keys()
	returnList = []
	copyKeys = stlKeys.__class__(stlKeys) #wlav suggested workaround. Make a copy first
	for x in copyKeys:
		k = x.c_str()
		returnList.append(k)
	return returnList

def getValues(item):
	keys = getKeys(item)
	returnList = []
	fv = None
	for key in keys:
		fv = None
		try:
			v = item.ValueAtKey(key).Value()
		except:
			raise Exception("Error: Could not retrieve a Value at the specified key ("+key+")")
		if (isinstance(v, int) or (isinstance(v, float))):
			fv = v
		elif (isinstance(v, cppyy.gbl.std.string)):
			fv = v.c_str()
		else:
			resultList = []
			for i in v:
				if isinstance(i.Value(), cppyy.gbl.std.string):
					resultList.append(i.Value().c_str())
				else:
					resultList.append(i.Value())
			fv = resultList
		returnList.append(fv)
	return returnList

def mergeDictionaries(sources):
	if isinstance(sources, list) == False:
		sources = [sources]
	sinkKeys = []
	sinkValues = []
	d = sources[0].GetDictionary()
	if d != None:
		stlKeys = d.Keys()
		if len(stlKeys) > 0:
			sinkKeys = getKeys(d)
			sinkValues = getValues(d)
	for i in range(1,len(sources)):
		d = sources[i].GetDictionary()
		if d == None:
			continue
		stlKeys = d.Keys()
		if len(stlKeys) > 0:
			sourceKeys = getKeys(d)
			for aSourceKey in sourceKeys:
				if aSourceKey not in sinkKeys:
					sinkKeys.append(aSourceKey)
					sinkValues.append("")
			for i in range(len(sourceKeys)):
				index = sinkKeys.index(sourceKeys[i])
				k = cppyy.gbl.std.string(sourceKeys[i])
				sourceValue = d.ValueAtKey(k).Value()
				if sourceValue != None:
					if sinkValues[index] != "":
						if isinstance(sinkValues[index], list):
							sinkValues[index].append(sourceValue)
						else:
							sinkValues[index] = [sinkValues[index], sourceValue]
					else:
						sinkValues[index] = sourceValue
	if len(sinkKeys) > 0 and len(sinkValues) > 0:
		stlKeys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
		for sinkKey in sinkKeys:
			stlKeys.push_back(sinkKey)
		stlValues = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
		for sinkValue in sinkValues:
			if isinstance(sinkValue, bool):
				stlValues.push_back(topologic.IntAttribute(sinkValue))
			elif isinstance(sinkValue, int):
				stlValues.push_back(topologic.IntAttribute(sinkValue))
			elif isinstance(sinkValue, float):
				stlValues.push_back(topologic.DoubleAttribute(sinkValue))
			elif isinstance(sinkValue, str):
				stlValues.push_back(topologic.StringAttribute(sinkValue))
			elif isinstance(sinkValue, list):
				l = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
				for v in sinkValue:
					if isinstance(v, bool):
						l.push_back(topologic.IntAttribute(v))
					elif isinstance(v, int):
						l.push_back(topologic.IntAttribute(v))
					elif isinstance(v, float):
						l.push_back(topologic.DoubleAttribute(v))
					elif isinstance(v, str):
						l.push_back(topologic.StringAttribute(v))
				stlValues.push_back(topologic.ListAttribute(l))
		newDict = topologic.Dictionary.ByKeysValues(stlKeys, stlValues)
		return newDict
	return None

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
						mDict = mergeDictionaries(sharedt)
						if mDict:
							e.SetDictionary(mDict)
						edges.push_back(e)
	if directApertures == True:
		cellmat = []
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
							apList = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
							_ = x.Apertures(ap)
							apList = list(ap)
							if len(apList) > 0:
								apTopList = []
								for ap in apList:
									apTopList.append(ap.Topology())
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
							mDict = mergeDictionaries(apTopList)
							if mDict:
								e.SetDictionary(mDict)
							edges.push_back(e)

	cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
	_ = topology.Cells(cells)
	if (viaSharedTopologies == True) or (viaSharedApertures == True) or (toExteriorTopologies == True) or (toExteriorApertures == True):
		for aCell in cells:
			if useInternalVertex == True:
				vCell = topologic.CellUtility.InternalVertex(aCell, tolerance)
			else:
				vCell = aCell.CenterOfMass()
			_ = vCell.SetDictionary(aCell.GetDictionary())
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
					_ = vst.SetDictionary(sharedTopology.GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))
			if viaSharedApertures:
				for sharedAperture in sharedApertures:
					if useInternalVertex == True:
						vst = internalVertex(sharedAperture.Topology(), tolerance)
					else:
						vst = sharedAperture.Topology().CenterOfMass()
					_ = vst.SetDictionary(sharedAperture.Topology().GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))
			if toExteriorTopologies:
				for exteriorTopology in exteriorTopologies:
					if useInternalVertex == True:
						vst = internalVertex(exteriorTopology, tolerance)
					else:
						vst = exteriorTopology.CenterOfMass()
					_ = vst.SetDictionary(exteriorTopology.GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))
			if toExteriorApertures:
				for exteriorAperture in exteriorApertures:
					extTop = exteriorAperture.Topology()
					if useInternalVertex == True:
						vst = internalVertex(extTop, tolerance)
					else:
						vst = exteriorAperture.Topology().CenterOfMass()
					_ = vst.SetDictionary(exteriorAperture.Topology().GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))

	for aCell in cells:
		if useInternalVertex == True:
			vCell = internalVertex(aCell, tolerance)
		else:
			vCell = aCell.CenterOfMass()
		_ = vCell.SetDictionary(aCell.GetDictionary())
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
					_ = vst.SetDictionary(exteriorTopology.GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vCell, vst))
			if toExteriorApertures:
				for exteriorAperture in exteriorApertures:
					extTop = exteriorAperture.Topology()
					if useInternalVertex == True:
						vst = internalVertex(extTop, tolerance)
					else:
						vst = exteriorAperture.Topology().CenterOfMass()
					_ = vst.SetDictionary(exteriorAperture.Topology().GetDictionary())
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

def processShell(item):
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
	facemat = []
	if direct == True:
		topFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = topology.Faces(topFaces)
		topFaces = list(topFaces)
		# Create a matrix of zeroes
		for i in range(len(topFaces)):
			faceRow = []
			for j in range(len(topFaces)):
				faceRow.append(0)
			facemat.append(faceRow)
		for i in range(len(topFaces)):
			for j in range(len(topFaces)):
				if (i != j) and facemat[i][j] == 0:
					facemat[i][j] = 1
					facemat[j][i] = 1
					sharedt = cppyy.gbl.std.list[topologic.Topology.Ptr]()
					topFaces[i].SharedTopologies(topFaces[j], 2, sharedt)
					sharedt = list(sharedt)
					if len(sharedt) > 0:
						if useInternalVertex == True:
							v1 = topologic.FaceUtility.InternalVertex(topFaces[i], tolerance)
							v2 = topologic.FaceUtility.InternalVertex(topFaces[j], tolerance)
						else:
							v1 = topFaces[i].CenterOfMass()
							v2 = topFaces[j].CenterOfMass()
						e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
						mDict = mergeDictionaries(sharedt)
						if mDict:
							e.SetDictionary(mDict)
						edges.push_back(e)
	if directApertures == True:
		facemat = []
		topFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
		_ = topology.Faces(topFaces)
		topFaces = list(topFaces)
		# Create a matrix of zeroes
		for i in range(len(topFaces)):
			faceRow = []
			for j in range(len(topFaces)):
				faceRow.append(0)
			facemat.append(faceRow)
		for i in range(len(topFaces)):
			for j in range(len(topFaces)):
				if (i != j) and facemat[i][j] == 0:
					facemat[i][j] = 1
					facemat[j][i] = 1
					sharedt = cppyy.gbl.std.list[topologic.Topology.Ptr]()
					topFaces[i].SharedTopologies(topFaces[j], 2, sharedt)
					sharedt = list(sharedt)
					if len(sharedt) > 0:
						apertureExists = False
						for x in sharedt:
							apList = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
							_ = x.Apertures(apList)
							if len(apList) > 0:
								apertureExists = True
								break
						if apertureExists:
							apTopList = []
							for ap in apList:
								apTopList.append(ap.Topology())
							if useInternalVertex == True:
								v1 = topologic.FaceUtility.InternalVertex(topFaces[i], tolerance)
								v2 = topologic.FaceUtility.InternalVertex(topFaces[j], tolerance)
							else:
								v1 = topFaces[i].CenterOfMass()
								v2 = topFaces[j].CenterOfMass()
							e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
							mDict = mergeDictionaries(apTopList)
							if mDict:
								e.SetDictionary(mDict)
							edges.push_back(e)

	topFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	_ = topology.Faces(topFaces)
	if (viaSharedTopologies == True) or (viaSharedApertures == True) or (toExteriorTopologies == True) or (toExteriorApertures == True):
		for aFace in topFaces:
			if useInternalVertex == True:
				vFace = topologic.FaceUtility.InternalVertex(aFace, tolerance)
			else:
				vFace = aFace.CenterOfMass()
			_ = vFace.SetDictionary(aFace.GetDictionary())
			vertices.push_back(vFace)
			fEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = aFace.Edges(fEdges)
			sharedTopologies = []
			exteriorTopologies = []
			sharedApertures = []
			exteriorApertures = []
			for anEdge in fEdges:
				faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
				_ = anEdge.Faces(faces)
				faces = list(faces)
				if len(faces) > 1:
					sharedTopologies.append(anEdge)
					apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
					_ = anEdge.Apertures(apertures)
					for anAperture in apertures:
						sharedApertures.append(anAperture)
				else:
					exteriorTopologies.append(anEdge)
					apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
					_ = anEdge.Apertures(apertures)
					for anAperture in apertures:
						exteriorApertures.append(anAperture)
			if viaSharedTopologies:
				for sharedTopology in sharedTopologies:
					if useInternalVertex == True:
						vst = internalVertex(sharedTopology, tolerance)
					else:
						vst = sharedTopology.CenterOfMass()
					_ = vst.SetDictionary(sharedTopology.GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vFace, vst))
			if viaSharedApertures:
				for sharedAperture in sharedApertures:
					if useInternalVertex == True:
						vst = internalVertex(sharedAperture.Topology(), tolerance)
					else:
						vst = sharedAperture.Topology().CenterOfMass()
					_ = vst.SetDictionary(sharedAperture.Topology().GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vFace, vst))
			if toExteriorTopologies:
				for exteriorTopology in exteriorTopologies:
					if useInternalVertex == True:
						vst = internalVertex(exteriorTopology, tolerance)
					else:
						vst = exteriorTopology.CenterOfMass()
					_ = vst.SetDictionary(exteriorTopology.GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vFace, vst))
			if toExteriorApertures:
				for exteriorAperture in exteriorApertures:
					extTop = exteriorAperture.Topology()
					if useInternalVertex == True:
						vst = internalVertex(extTop, tolerance)
					else:
						vst = exteriorAperture.Topology().CenterOfMass()
					_ = vst.SetDictionary(exteriorAperture.Topology().GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vFace, vst))

	for aFace in topFaces:
		if useInternalVertex == True:
			vFace = internalVertex(aFace, tolerance)
		else:
			vFace = aFace.CenterOfMass()
		_ = vFace.SetDictionary(aFace.GetDictionary())
		vertices.push_back(vFace)
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

def processFace(item):
	face = item[0]
	toExteriorTopologies = item[5]
	toExteriorApertures = item[6]
	useInternalVertex = item[7]
	tolerance = item[8]
	graph = None
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()

	if useInternalVertex == True:
		vFace = topologic.FaceUtility.InternalVertex(face, tolerance)
	else:
		vFace = face.CenterOfMass()
	_ = vFace.SetDictionary(face.GetDictionary())

	if (toExteriorTopologies == True) or (toExteriorApertures == True):
		vertices.push_back(vFace)
		fEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		_ = face.Edges(fEdges)
		exteriorTopologies = []
		exteriorApertures = []
		for anEdge in fEdges:
			exteriorTopologies.append(anEdge)
			apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
			_ = anEdge.Apertures(apertures)
			for anAperture in apertures:
				exteriorApertures.append(anAperture)
			if toExteriorTopologies:
				for exteriorTopology in exteriorTopologies:
					if useInternalVertex == True:
						vst = internalVertex(exteriorTopology, tolerance)
					else:
						vst = exteriorTopology.CenterOfMass()
					_ = vst.SetDictionary(exteriorTopology.GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vFace, vst))
			if toExteriorApertures:
				for exteriorAperture in exteriorApertures:
					extTop = exteriorAperture.Topology()
					if useInternalVertex == True:
						vst = internalVertex(extTop, tolerance)
					else:
						vst = exteriorAperture.Topology().CenterOfMass()
					_ = vst.SetDictionary(exteriorAperture.Topology().GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vFace, vst))
	else:
		vertices.push_back(vFace)

	finalTopologies = cppyy.gbl.std.list[topologic.Topology.Ptr]()
	if len(list(edges)) > 0:
		for e in edges:
			finalTopologies.push_back(e)
		cluster = topologic.Cluster.ByTopologies(finalTopologies)
		cluster = cluster.SelfMerge()
		graph = topologic.Graph.ByTopology(cluster, True, False, False, False, False, False, tolerance)
		return graph
	else:
		graph = topologic.Graph.ByTopology(vFace, True, False, False, False, False, False, tolerance)
		return graph
	return None

def processWire(item):
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
	edgemat = []
	if direct == True:
		topEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		_ = topology.Edges(topEdges)
		topEdges = list(topEdges)
		# Create a matrix of zeroes
		for i in range(len(topEdges)):
			edgeRow = []
			for j in range(len(topEdges)):
				edgeRow.append(0)
			edgemat.append(edgeRow)
		for i in range(len(topEdges)):
			for j in range(len(topEdges)):
				if (i != j) and edgemat[i][j] == 0:
					edgemat[i][j] = 1
					edgemat[j][i] = 1
					sharedt = cppyy.gbl.std.list[topologic.Topology.Ptr]()
					topEdges[i].SharedTopologies(topEdges[j], 1, sharedt)
					sharedt = list(sharedt)
					if len(sharedt) > 0:
						try:
							v1 = topologic.EdgeUtility.PointAtParameter(topEdges[i], 0.5)
						except:
							v1 = topEdges[j].CenterOfMass()
						try:
							v2 = topologic.EdgeUtility.PointAtParameter(topEdges[j], 0.5)
						except:
							v2 = topEdges[j].CenterOfMass()
						e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
						mDict = mergeDictionaries(sharedt)
						if mDict:
							e.SetDictionary(mDict)
						edges.push_back(e)
	if directApertures == True:
		edgemat = []
		topEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		_ = topology.Edges(topEdges)
		topEdges = list(topEdges)
		# Create a matrix of zeroes
		for i in range(len(topEdges)):
			edgeRow = []
			for j in range(len(topEdges)):
				edgeRow.append(0)
			edgemat.append(edgeRow)
		for i in range(len(topEdges)):
			for j in range(len(topEdges)):
				if (i != j) and edgemat[i][j] == 0:
					edgemat[i][j] = 1
					edgemat[j][i] = 1
					sharedt = cppyy.gbl.std.list[topologic.Topology.Ptr]()
					topEdges[i].SharedTopologies(topEdges[j], 1, sharedt)
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
							try:
								v1 = topologic.EdgeUtility.PointAtParameter(topEdges[i], 0.5)
							except:
								v1 = topEdges[j].CenterOfMass()
							try:
								v2 = topologic.EdgeUtility.PointAtParameter(topEdges[j], 0.5)
							except:
								v2 = topEdges[j].CenterOfMass()
							e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
							mDict = mergeDictionaries(ap.Topology())
							if mDict:
								e.SetDictionary(mDict)
							edges.push_back(e)

	topEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	_ = topology.Edges(topEdges)
	if (viaSharedTopologies == True) or (viaSharedApertures == True) or (toExteriorTopologies == True) or (toExteriorApertures == True):
		for anEdge in topEdges:
			try:
				vEdge = topologic.EdgeUtility.PointAtParameter(anEdge, 0.5)
			except:
				vEdge = anEdge.CenterOfMass()
			_ = vEdge.SetDictionary(anEdge.GetDictionary())
			vertices.push_back(vEdge)
			vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			_ = anEdge.Vertices(vertices)
			sharedTopologies = []
			exteriorTopologies = []
			sharedApertures = []
			exteriorApertures = []
			for aVertex in vertices:
				edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
				_ = aVertex.Edges(edges)
				edges = list(edges)
				if len(edges) > 1:
					sharedTopologies.append(aVertex)
					apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
					_ = aVertex.Apertures(apertures)
					for anAperture in apertures:
						sharedApertures.append(anAperture)
				else:
					exteriorTopologies.append(aVertex)
					apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
					_ = aVertex.Apertures(apertures)
					for anAperture in apertures:
						exteriorApertures.append(anAperture)
			if viaSharedTopologies:
				for sharedTopology in sharedTopologies:
					vertices.push_back(sharedTopology)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vEdge, sharedTopology))
			if viaSharedApertures:
				for sharedAperture in sharedApertures:
					if useInternalVertex == True:
						vst = internalVertex(sharedAperture.Topology(), tolerance)
					else:
						vst = sharedAperture.Topology().CenterOfMass()
					_ = vst.SetDictionary(sharedAperture.GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vEdge, vst))
			if toExteriorTopologies:
				for exteriorTopology in exteriorTopologies:
					vertices.push_back(exteriorTopology)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vEdge, exteriorTopology))
			if toExteriorApertures:
				for exteriorAperture in exteriorApertures:
					extTop = exteriorAperture.Topology()
					if useInternalVertex == True:
						vst = internalVertex(extTop, tolerance)
					else:
						vst = exteriorAperture.Topology().CenterOfMass()
					_ = vst.SetDictionary(exteriorAperture.Topology().GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vEdge, vst))

	for anEdge in topEdges:
		try:
			vEdge = topologic.EdgeUtility.PointAtParameter(anEdge, 0.5)
		except:
			vEdge = anEdge.CenterOfMass()
		_ = vEdge.SetDictionary(anEdge.GetDictionary())
		vertices.push_back(vEdge)
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

def processEdge(item):
	edge = item[0]
	toExteriorTopologies = item[5]
	toExteriorApertures = item[6]
	useInternalVertex = item[7]
	tolerance = item[8]
	graph = None
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()

	if useInternalVertex == True:
		try:
			vEdge = topologic.EdgeUtility.PointAtParameter(edge, 0.5)
		except:
			vEdge = edge.CenterOfMass()
	else:
		vEdge = edge.CenterOfMass()
	_ = vEdge.SetDictionary(edge.GetDictionary())

	if (toExteriorTopologies == True) or (toExteriorApertures == True):
		vertices.push_back(vFace)
		eVertices = cppyy.gbl.std.list[topologic.Edge.Ptr]()
		_ = edge.Vertices(eVertices)
		exteriorTopologies = []
		exteriorApertures = []
		for aVertex in eVertices:
			exteriorTopologies.append(aVertex)
			apertures = cppyy.gbl.std.list[topologic.Aperture.Ptr]()
			_ = aVertex.Apertures(apertures)
			for anAperture in apertures:
				exteriorApertures.append(anAperture)
			if toExteriorTopologies:
				for exteriorTopology in exteriorTopologies:
					if useInternalVertex == True:
						vst = internalVertex(exteriorTopology, tolerance)
					else:
						vst = exteriorTopology.CenterOfMass()
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vEdge, vst))
			if toExteriorApertures:
				for exteriorAperture in exteriorApertures:
					extTop = exteriorAperture.Topology()
					if useInternalVertex == True:
						vst = internalVertex(extTop, tolerance)
					else:
						vst = exteriorAperture.Topology().CenterOfMass()
					_ = vst.SetDictionary(exteriorAperture.Topology().GetDictionary())
					vertices.push_back(vst)
					edges.push_back(topologic.Edge.ByStartVertexEndVertex(vEdge, vst))
	else:
		vertices.push_back(vEdge)

	finalTopologies = cppyy.gbl.std.list[topologic.Topology.Ptr]()
	if len(list(edges)) > 0:
		for e in edges:
			finalTopologies.push_back(e)
		cluster = topologic.Cluster.ByTopologies(finalTopologies)
		cluster = cluster.SelfMerge()
		graph = topologic.Graph.ByTopology(cluster, True, False, False, False, False, False, tolerance)
		return graph
	else:
		graph = topologic.Graph.ByTopology(vFace, True, False, False, False, False, False, tolerance)
		return graph
	return None

def processVertex(item):
	vertex = item[0]
	tolerance = item[8]
	return topologic.Graph.ByTopology(vertex, True, False, False, False, False, False, tolerance)

def processItem(item):
	topology = item[0]
	graph = None
	if topology:
		classType = topology.GetType()
		if classType == 64: #CellComplex
			graph = processCellComplex(item)
		elif classType == 32: #Cell
			graph = processCell(item)
		elif classType == 16: #Shell
			graph = processShell(item)
		elif classType == 8: #Face
			graph = processFace(item)
		elif classType == 4: #Wire
			graph = processWire(item)
		elif classType == 2: #Edge
			graph = processEdge(item)
		elif classType == 1: #Vertex
			graph = processVertex(item)
		elif classType == 128: #Cluster
			raise Exception("ERROR: Graph.ByTopology: Cluster is not supported. Decompose into its sub-topologies first.")
	return graph

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

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
	ToExteriorTopologiesProp: BoolProperty(name="To Exterior Topologies", default=False, update=updateNode)
	ToExteriorAperturesProp: BoolProperty(name="To Exterior Apertures", default=False, update=updateNode)
	UseInternalVertexProp: BoolProperty(name="Use Internal Vertex", default=False, update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

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

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Graph'].sv_set([])
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		directList = self.inputs['Direct'].sv_get(deepcopy=True)
		directAperturesList = self.inputs['DirectIfSharedApertures'].sv_get(deepcopy=True)
		viaSharedTopologiesList = self.inputs['ViaSharedTopologies'].sv_get(deepcopy=True)
		viaSharedAperturesList = self.inputs['ViaSharedApertures'].sv_get(deepcopy=True)
		toExteriorTopologiesList = self.inputs['ToExteriorTopologies'].sv_get(deepcopy=True)
		toExteriorAperturesList = self.inputs['ToExteriorApertures'].sv_get(deepcopy=True)
		useInternalVertexList = self.inputs['UseInternalVertex'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)

		topologyList = flatten(topologyList)
		directList = flatten(directList)
		directAperturesList = flatten(directAperturesList)
		viaSharedTopologiesList = flatten(viaSharedTopologiesList)
		viaSharedAperturesList = flatten(viaSharedAperturesList)
		toExteriorTopologiesList = flatten(toExteriorTopologiesList)
		toExteriorAperturesList = flatten(toExteriorAperturesList)
		useInternalVertexList = flatten(useInternalVertexList)
		toleranceList = flatten(toleranceList)
		inputs = [topologyList, directList, directAperturesList, viaSharedTopologiesList, viaSharedAperturesList, toExteriorTopologiesList, toExteriorAperturesList, useInternalVertexList, toleranceList]
		outputs = []
		if ((self.Replication) == "Default"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Graph'].sv_set(outputs)
		end = time.time()
		print("Graph.ByTopology Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphByTopology)

def unregister():
    bpy.utils.unregister_class(SvGraphByTopology)
