import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
try:
	import openstudio
except:
	raise Exception("Error: Could not import openstudio.")
import os

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
			# print(base,y)
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




import numpy as np
import ifcopenshell
import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary, VertexUtility, EdgeUtility, FaceUtility, CellUtility, TopologyUtility
import ifcopenshell.api
import openstudio

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

def getCell(settings, product):
  shape = ifcopenshell.geom.create_shape(settings, product)
  brepString = shape.geometry.brep_data
  topology = Topology.ByString(brepString)

  return getSubTopologies(topology, Cell)[0]

def getSubTopologies(topology, subTopologyClass):
  subtopologies = []

  if subTopologyClass == Vertex:
    _ = topology.Vertices(None, subtopologies)
  elif subTopologyClass == Edge:
    _ = topology.Edges(None, subtopologies)
  elif subTopologyClass == Wire:
    _ = topology.Wires(None, subtopologies)
  elif subTopologyClass == Face:
    _ = topology.Faces(None, subtopologies)
  elif subTopologyClass == Shell:
    _ = topology.Shells(None, subtopologies)
  elif subTopologyClass == Cell:
    _ = topology.Cells(None, subtopologies)
  elif subTopologyClass == CellComplex:
    _ = topology.CellComplexes(None, subtopologies)

  return subtopologies

def setDictionary(elem, key, value):
  dictionary = elem.GetDictionary()
  dictionary.Add(key, topologic.StringAttribute(value))
  elem.SetDictionary(dictionary)

def getDictionary(elem, key):
  dictionary = elem.GetDictionary()
  if dictionary.ContainsKey(key):
    value = dictionary.ValueAtKey(key)
    return value.StringValue()
  return None

def removeDictionary(elem, key):
  dictionary = elem.GetDictionary()
  dictionary.Remove(key)
  elem.SetDictionary(dictionary)

def boolean(topologyA, topologyB, operation):
  topologyC = None

  try:
    if operation == "Union":
      topologyC = topologyA.Union(topologyB, False)
    elif operation == "Difference":
      topologyC = topologyA.Difference(topologyB, False)
    elif operation == "Intersect":
      topologyC = topologyA.Intersect(topologyB, False)
    elif operation == "SymDif":
      topologyC = topologyA.XOR(topologyB, False)
    elif operation == "Merge":
      topologyC = topologyA.Merge(topologyB, False)

    if not topologyC:
      return None
  except:
    return None

  return topologyC

def meshData(topology):
  vertices = []
  faces = []
  if topology is None:
    return [vertices, faces]

  topVerts = []
  if (topology.Type() == 1): #input is a vertex, just add it and process it
    topVerts.append(topology)
  else:
    _ = topology.Vertices(None, topVerts)
  for aVertex in topVerts:
    try:
      vertices.index(tuple([aVertex.X(), aVertex.Y(), aVertex.Z()])) # Vertex already in list
    except:
      vertices.append(tuple([aVertex.X(), aVertex.Y(), aVertex.Z()])) # Vertex not in list, add it.

  topFaces = []
  if (topology.Type() == 8): # Input is a Face, just add it and process it
    topFaces.append(topology)
  elif (topology.Type() > 8):
    _ = topology.Faces(None, topFaces)
  for aFace in topFaces:
    wires = []
    ib = []
    _ = aFace.InternalBoundaries(ib)
    if(len(ib) > 0):
      triFaces = []
      FaceUtility.Triangulate(aFace, 0.0, triFaces)
      for aTriFace in triFaces:
        wires.append(aTriFace.ExternalBoundary())
    else:
      wires.append(aFace.ExternalBoundary())

    for wire in wires:
      f = []
      for aVertex in getSubTopologies(wire, Vertex):
        try:
          fVertexIndex = vertices.index(tuple([aVertex.X(), aVertex.Y(), aVertex.Z()]))
        except:
          vertices.append(tuple([aVertex.X(), aVertex.Y(), aVertex.Z()]))
          fVertexIndex = len(vertices)-1
        f.append(fVertexIndex)

      p = np.array(vertices[f[0]])
      u = normalize(np.array(vertices[f[1]] - p))
      v = np.array(vertices[f[-1]]) - p
      normal = FaceUtility.NormalAtParameters(aFace, 0.5, 0.5)
      if normalize(np.cross(u, v)) @ np.array([normal[0], normal[1], normal[2]]) + 1 < 1e-6:
        f.reverse()

      faces.append(tuple(f))

  return [vertices, faces]

def normalize(u):
  return u / np.linalg.norm(u)

def createIfcFaceSurface(ifc_file, element_matrix, vertices, face):
  element_vertices = [np.linalg.solve(element_matrix, np.array(v+(1,)))[:-1] for v in vertices]

  p = element_vertices[face[0]]
  u = normalize(element_vertices[face[1]] - p)
  v = element_vertices[face[-1]] - p
  n = normalize(np.cross(u, v))
  plane = ifc_file.createIfcPlane(
    ifc_file.createIfcAxis2Placement3D(
      ifc_file.createIfcCartesianPoint(p.tolist()),
      ifc_file.createIfcDirection(n.tolist()),
      ifc_file.createIfcDirection(u.tolist()),
    )
  )

  plane_matrix = ifcopenshell.util.placement.get_axis2placement(plane.Position)
  poly_loop = ifc_file.createIfcPolyLoop([ifc_file.createIfcCartesianPoint(np.linalg.solve(plane_matrix, np.append(element_vertices[f],1))[:2].tolist()) for f in face])
  face_bound = [ifc_file.createIfcFaceOuterBound(poly_loop, True)]

  return ifc_file.createIfcFaceSurface(face_bound, plane, True)

def createConnectionSurfaceGeometry(ifc_file, relating_elem, related_elem, vertices, face):
  connection_surface = ifc_file.create_entity("IfcConnectionSurfaceGeometry")
  relating_matrix = ifcopenshell.util.placement.get_local_placement(relating_elem.ObjectPlacement)
  connection_surface.SurfaceOnRelatingElement = createIfcFaceSurface(ifc_file, relating_matrix, vertices, face)
  related_matrix = ifcopenshell.util.placement.get_local_placement(related_elem.ObjectPlacement)
  connection_surface.SurfaceOnRelatedElement = createIfcFaceSurface(ifc_file, related_matrix, vertices, face)

  return connection_surface

def createRelConnectsElements(ifc_file, relating_elem, related_elem, vertices, face):
  rel_connects = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class="IfcRelConnectsElements")
  rel_connects.ConnectionGeometry = createConnectionSurfaceGeometry(ifc_file, relating_elem, related_elem, vertices, face)
  rel_connects.RelatingElement = relating_elem
  rel_connects.RelatedElement = related_elem

  return rel_connects

def getValueAtKey(dict, key):
	returnValue = None
	try:
		returnValue = key
	except:
		returnValue = None
	return returnValue

def relevantSelector(topology):
	returnVertex = None
	if topology.Type() == topologic.Vertex.Type():
		return topology
	elif topology.Type() == topologic.Edge.Type():
		return topologic.EdgeUtility.PointAtParameter(topology, 0.5)
	elif topology.Type() == topologic.Face.Type():
		return topologic.FaceUtility.InternalVertex(topology, 0.0001)
	elif topology.Type() == topologic.Cell.Type():
		return topologic.CellUtility.InternalVertex(topology, 0.0001)
	else:
		return topology.Centroid()

def topologyContains(topology, vertex, tol):
	contains = False
	if topology.Type() == topologic.Vertex.Type():
		try:
			contains = (topologic.VertexUtility.Distance(sourceVertex, vertex) <= tol)
		except:
			contains = False
		return contains
	elif topology.Type() == topologic.Edge.Type():
		try:
			_ = topologic.EdgeUtility.ParameterAtPoint(topology, vertex)
			contains = True
		except:
			contains = False
		return contains
	elif topology.Type() == topologic.Face.Type():
		return topologic.FaceUtility.IsInside(topology, vertex, tol)
	elif topology.Type() == topologic.Cell.Type():
		return (topologic.CellUtility.Contains(topology, vertex, tol) == 0)
	return False

def transferDictionaries(sources, sinks, tol):
	for sink in sinks:
		sinkKeys = []
		sinkValues = []
		iv = relevantSelector(sink)
		j = 1
		for source in sources:
			if topologyContains(source, iv, tol):
				d = source.GetDictionary()
				stl_keys = d.Keys()
				if len(stl_keys) > 0:
					sourceKeys = d.Keys()
					for aSourceKey in sourceKeys:
						if aSourceKey not in sinkKeys:
							sinkKeys.append(aSourceKey)
							sinkValues.append("")
					for i in range(len(sourceKeys)):
						index = sinkKeys.index(sourceKeys[i])
						sourceValue = getDictionary(source, sourceKeys[i])
						if sourceValue != None:
							if sinkValues[index] != "":
								sinkValues[index] = sinkValues[index]+","+sourceValue
							else:
								sinkValues[index] = sourceValue
		if len(sinkKeys) > 0 and len(sinkValues) > 0:
			stl_keys = []
			for key in sinkKeys:
				stl_keys.append(key)
			stlValues = []
			for value in sinkValues:
				stlValues.append(topologic.StringAttribute(value))
			newDict = topologic.Dictionary.ByKeysValues(stl_keys, stlValues)
			_ = sink.SetDictionary(newDict)

def createRelSpaceBoundary(ifc_file, ifc_class, ifc_space, ifc_building_element, vertices, f, boundary_condition):
  ifc_rel_space_boundary = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class=ifc_class)
  ifc_rel_space_boundary.Name = "Boundary " + str(len(ifc_file.by_type("IfcRelSpaceBoundary")) - 1)
  ifc_rel_space_boundary.RelatingSpace = ifc_space
  ifc_rel_space_boundary.RelatedBuildingElement = ifc_building_element
  ifc_rel_space_boundary.ConnectionGeometry = createConnectionSurfaceGeometry(ifc_file, ifc_space, ifc_building_element, vertices, f)
  ifc_rel_space_boundary.PhysicalOrVirtualBoundary = "PHYSICAL"
  ifc_rel_space_boundary.InternalOrExternalBoundary = boundary_condition

  return ifc_rel_space_boundary

def createRelSpaceBoundary1and2a(ifc_file, top_space_boundary, reverse, ifc_space, other_ifc_space, ifc_building_element, space_boundary_2b):
  ifc_rel_space_boundary = None
  if ifc_space is not None:
    vertices, fs = meshData(top_space_boundary)
    f = fs[0][::-1] if reverse else fs[0]

    if other_ifc_space is None:
      ifc_rel_space_boundary = createRelSpaceBoundary(ifc_file, "IfcRelSpaceBoundary1stLevel", ifc_space, ifc_building_element, vertices, f, "EXTERNAL")
    else:
      ifc_rel_space_boundary = createRelSpaceBoundary(ifc_file, "IfcRelSpaceBoundary2ndLevel", ifc_space, ifc_building_element, vertices, f, "INTERNAL")
    space_boundary_2b = boolean(space_boundary_2b, top_space_boundary, "Difference")

  return [ifc_rel_space_boundary, space_boundary_2b]

def createInnerBoundary(ifc_rel_space_boundary, top_opening_element, top_space_boundary, reverse):
  if ifc_rel_space_boundary is None:
    return None

  top_inner_boundary = boolean(top_space_boundary, top_opening_element, "Intersect")
  if top_inner_boundary is None:
    return None

  vertices, fs = meshData(top_inner_boundary)
  f = fs[0][::-1] if reverse else fs[0]

  ifc_element = ifc_file.by_guid(getDictionary(top_opening_element, "IfcElement"))
  ifc_inner_boundary = createRelSpaceBoundary(
    ifc_file, ifc_rel_space_boundary.is_a(), ifc_rel_space_boundary.RelatingSpace, ifc_element, vertices, f, ifc_rel_space_boundary.InternalOrExternalBoundary)
  ifc_inner_boundary.ParentBoundary = ifc_rel_space_boundary

  return ifc_inner_boundary

def getVertices(ifc_space_boundary, space_matrix):
  ifc_face_surface = ifc_space_boundary.ConnectionGeometry.SurfaceOnRelatingElement
  plane_vertices = [v.Coordinates for v in ifc_face_surface.Bounds[0].Bound.Polygon]
  plane_matrix = ifcopenshell.util.placement.get_axis2placement(ifc_face_surface.FaceSurface.Position)
  element_vertices = [(plane_matrix @ np.array(v+(0,1))) for v in plane_vertices]
  vertices = [space_matrix @ v for v in element_vertices]

  return [openstudio.Point3d(v[0], v[1], v[2]) for v in vertices]

def processItem(item):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_BREP_DATA, True)
    settings.set(settings.SEW_SHELLS, True)
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)

    ifc_file = ifcopenshell.open("C:/BIM2BEM/ExternalEarth_R20_IFC4.ifc")

    body_context = next((item  for item  in ifc_file.by_type("IfcGeometricRepresentationSubContext") if item.ContextIdentifier == "Body"), None)
    top_building = None
    if body_context is None:
      parent_context = next((item  for item  in ifc_file.by_type("IfcGeometricRepresentationContext") if item.ContextType == "Model"), None)
      body_context = ifc_file.createIfcGeometricRepresentationSubContext("Body", "Model", None, None, None, None, parent_context, None, "MODEL_VIEW", None)

    ifc_building_element_cells = []
    for ifc_building_element in ifc_file.by_type('IfcBuildingElement'):
      if not (ifc_building_element.is_a('IfcWall') or ifc_building_element.is_a('IfcSlab')):
        continue

      ifc_building_element_cell = getCell(settings, ifc_building_element)
      setDictionary(ifc_building_element_cell, "IfcBuildingElement", ifc_building_element.GlobalId)
      ifc_building_element_cells.append(ifc_building_element_cell)

      int_bounds = []
      ifc_building_element_cell.InternalBoundaries(int_bounds)
      for shell in int_bounds:
        md = meshData(shell)
        for f in md[1]:
          createRelConnectsElements(ifc_file, ifc_building_element, ifc_building_element, md[0], f)
    top_building = CellComplex.ByCells(ifc_building_element_cells)
    transferDictionaries(ifc_building_element_cells, getSubTopologies(top_building, Cell), 1e-3)

    for face in getSubTopologies(top_building, Face):
      ajacent_cells = []
      _ = FaceUtility.AdjacentCells(face, top_building, ajacent_cells)
      ajacent_cells = list(ajacent_cells)
      if len(ajacent_cells) > 1:
        relating_elem = ifc_file.by_guid(getDictionary(ajacent_cells[0], "IfcBuildingElement"))
        related_elem = ifc_file.by_guid(getDictionary(ajacent_cells[1], "IfcBuildingElement"))
        md = meshData(face)
        createRelConnectsElements(ifc_file, relating_elem, related_elem, md[0], md[1][0])
      else:
        ifc_building_element = ifc_file.by_guid(getDictionary(ajacent_cells[0], "IfcBuildingElement"))
        setDictionary(face, "IfcBuildingElement", ifc_building_element.GlobalId)

    cells = []
    ext_boundary = getSubTopologies(top_building, CellComplex)[0].ExternalBoundary()
    transferDictionaries(getSubTopologies(top_building, Face), getSubTopologies(ext_boundary, Face), 1e-3)
    for shell in getSubTopologies(ext_boundary, Shell):
      cell = Cell.ByShell(shell)
      if CellUtility.Volume(cell) < 1e-6:
        continue

      cell_storey, elevation = None, None
      for face in getSubTopologies(shell, Face):
        ifc_building_element = ifc_file.by_guid(getDictionary(face, "IfcBuildingElement"))
        if not ifc_building_element.ContainedInStructure:
          ifc_building_element = ifc_building_element.Decomposes[0].RelatingObject
        ifc_building_storey = ifc_building_element.ContainedInStructure[0].RelatingStructure
        if elevation is None or ifc_building_storey.Elevation < elevation:
          cell_storey, elevation = ifc_building_storey, ifc_building_storey.Elevation
      transferDictionaries(getSubTopologies(shell, Face), getSubTopologies(cell, Face), 1e-3)
      setDictionary(cell, "IfcBuildingStorey", cell_storey.GlobalId)
      cells.append(cell)

    cells.sort(key=lambda cell: CellUtility.Volume(cell))
    for idx_space, cell in enumerate(cells[:-1]):
      ifc_space = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class="IfcSpace")
      ifc_space.CompositionType = "ELEMENT"
      ifc_space.PredefinedType = "INTERNAL"
      ifc_building_storey = ifc_file.by_guid(getDictionary(cell, "IfcBuildingStorey"))
      ifc_space.Name = "Space " + str(len(ifc_file.by_type('IfcSpace')) - 1)
      ifcopenshell.api.run("aggregate.assign_object", ifc_file, product=ifc_space, relating_object=ifc_building_storey)
      md = meshData(cell)
      o, z = None, None
      for v in md[0]:
        if z is None or v[-1] < z:
          o, z = v, v[-1]
      space_matrix = np.linalg.solve(ifcopenshell.util.placement.get_local_placement(ifc_building_storey.ObjectPlacement), ifcopenshell.util.placement.a2p(o, np.array([0,0,1]), np.array([1,0,0])))
      point_list = ifc_file.createIfcCartesianPointList3D([np.linalg.solve(space_matrix, np.append(v,1))[:-1].tolist() for v in md[0]])
      indexed_faces = [ifc_file.createIfcIndexedPolygonalFace([index + 1 for index in f]) for f in md[1]]
      representation = ifc_file.createIfcPolygonalFaceSet(point_list, None, indexed_faces, None)
      shape = ifc_file.createIfcShapeRepresentation(body_context, body_context.ContextIdentifier, "Tessellation", [representation])
      ifcopenshell.api.run("geometry.assign_representation", ifc_file, product=ifc_space, representation=shape)
      ifcopenshell.api.run("geometry.edit_object_placement", ifc_file, product=ifc_space, matrix=space_matrix)
      for face in getSubTopologies(cell, Face):
        setDictionary(face, "IfcSpace", ifc_space.GlobalId)
      transferDictionaries(getSubTopologies(cell, Face), getSubTopologies(top_building, Face), 1e-3)

    for cell in getSubTopologies(top_building, Cell):
      ifc_building_element = ifc_file.by_guid(getDictionary(cell, "IfcBuildingElement"))
      faces = [face for face in getSubTopologies(cell, Face) if ifc_file.by_guid(getDictionary(face, "IfcBuildingElement")) is not None]

      top_opening_elements = []
      for ifc_rel_voids_element in ifc_building_element.HasOpenings:
        ifc_opening_element = ifc_rel_voids_element.RelatedOpeningElement
        top_opening_element = getCell(settings, ifc_opening_element)
        if not ifc_opening_element.HasFillings:
          continue

        setDictionary(top_opening_element, "IfcElement", ifc_opening_element.HasFillings[0].RelatedBuildingElement.GlobalId)
        top_opening_elements.append(top_opening_element)

      space_boundary_2bs = [face for face in faces]
      for idx, face in enumerate(faces):
        normal = FaceUtility.NormalAtParameters(face, 0.5, 0.5)
        n = np.array([normal[0], normal[1], normal[2]])
        point = FaceUtility.VertexAtParameters(face, 0.5, 0.5)
        p = np.array([point.X(), point.Y(), point.Z()])
        d = np.dot(n, p)

        ifc_space = ifc_file.by_guid(getDictionary(face, "IfcSpace"))
        for other_idx, other_face in enumerate(faces[idx+1:]):
          other_normal = FaceUtility.NormalAtParameters(other_face, 0.5, 0.5)
          other_n = np.array([other_normal[0], other_normal[1], other_normal[2]])
          if np.dot(n, other_n) + 1 > 1e-6:
            continue

          other_point = FaceUtility.VertexAtParameters(other_face, 0.5, 0.5)
          other_p = np.array([other_point.X(), other_point.Y(), other_point.Z()])
          dist = -np.dot(n, other_p) + d
          if dist < 1e-6:
            continue

          top_space_boundary = boolean(face, TopologyUtility.Translate(other_face, dist*normal[0], dist*normal[1], dist*normal[2]), "Intersect")
          if top_space_boundary is None:
            continue

          top_space_boundary = getSubTopologies(top_space_boundary, Face)
          if not top_space_boundary:
            continue

          top_space_boundary = top_space_boundary[0]
          other_ifc_space = ifc_file.by_guid(getDictionary(faces[idx+other_idx+1], "IfcSpace"))
          ifc_rel_space_boundary, space_boundary_2bs[idx] = createRelSpaceBoundary1and2a(
            ifc_file, top_space_boundary, True, ifc_space, other_ifc_space, ifc_building_element, space_boundary_2bs[idx])
          other_top_space_boundary = getSubTopologies(TopologyUtility.Translate(top_space_boundary, -dist*normal[0], -dist*normal[1],-dist*normal[2]), Face)[0]
          other_ifc_rel_space_boundary, space_boundary_2bs[idx+other_idx+1] = createRelSpaceBoundary1and2a(
            ifc_file, other_top_space_boundary, False, other_ifc_space, ifc_space, ifc_building_element, space_boundary_2bs[idx+other_idx+1])

          if ifc_rel_space_boundary is not None and other_ifc_rel_space_boundary is not None:
            ifc_rel_space_boundary.CorrespondingBoundary = other_ifc_rel_space_boundary
            other_ifc_rel_space_boundary.CorrespondingBoundary = ifc_rel_space_boundary

          for top_opening_element in top_opening_elements:
            ifc_inner_boundary = createInnerBoundary(ifc_rel_space_boundary, top_opening_element, top_space_boundary, True)
            other_ifc_inner_boundary = createInnerBoundary(other_ifc_rel_space_boundary, top_opening_element, other_top_space_boundary, False)

            if ifc_inner_boundary is not None and other_ifc_inner_boundary is not None:
              ifc_inner_boundary.CorrespondingBoundary = other_ifc_inner_boundary
              other_ifc_inner_boundary.CorrespondingBoundary = ifc_inner_boundary

      for face, space_boundary_2b in zip(faces, space_boundary_2bs):
        ifc_space = ifc_file.by_guid(getDictionary(face, "IfcSpace"))
        if ifc_space is not None:
          vertices, fs = meshData(space_boundary_2b)
          for f in fs:
            createRelSpaceBoundary(ifc_file, "IfcRelSpaceBoundary2ndLevel", ifc_space, ifc_building_element, vertices, f[::-1], "INTERNAL")

    ifc_file.write("C:/BIM2BEM/output.ifc")

    # model = openstudio.model.Model()
    # ifc2os = {}

    # for ifc_material_layer in ifc_file.by_type('IfcMaterialLayer'):
      # if not ifc_material_layer.ToMaterialLayerSet:
        # continue

      # os_standard_opaque_material = openstudio.model.StandardOpaqueMaterial(model)
      # os_standard_opaque_material.setName(ifc_material_layer.Name)
      # os_standard_opaque_material.setThickness(float(ifc_material_layer.LayerThickness))
      # ifc2os[ifc_material_layer] = os_standard_opaque_material

    # for ifc_material_layer_set in ifc_file.by_type('IfcMaterialLayerSet'):
      # if not ifc_material_layer_set.AssociatedTo:
        # continue

      # os_construction = openstudio.model.Construction(model)
      # os_construction.setName(ifc_material_layer_set.LayerSetName)
      # os_construction.setLayers([ifc2os[ifc_material_layer] for ifc_material_layer in ifc_material_layer_set.MaterialLayers])
      # ifc2os[ifc_material_layer_set] = os_construction

    # for ifc_building_storey in ifc_file.by_type('IfcBuildingStorey'):
      # if not ifc_building_storey.IsDecomposedBy:
        # continue

      # ifc_spaces = [x for x in ifc_building_storey.IsDecomposedBy[0].RelatedObjects if x.is_a("IfcSpace")]
      # if not ifc_spaces:
        # continue

      # os_building_story = openstudio.model.BuildingStory(model)
      # os_building_story.setName(ifc_building_storey.Name)
      # os_building_story.setNominalZCoordinate(float(ifc_building_storey.Elevation))
      # for ifc_space in ifc_spaces:
        # os_space = openstudio.model.Space(model)
        # os_space.setName(ifc_space.Name)
        # os_space.setBuildingStory(os_building_story)
        # space_matrix = ifcopenshell.util.placement.get_local_placement(ifc_space.ObjectPlacement)
        # for ifc_space_boundary in ifc_space.BoundedBy:
          # if ifc_space_boundary.ParentBoundary is not None:
            # continue

          # os_surface = openstudio.model.Surface(getVertices(ifc_space_boundary, space_matrix), model)
          # os_surface.setName(ifc_space_boundary.Name)
          # os_surface.setSpace(os_space)
          # if ifc_space_boundary.InternalOrExternalBoundary == "INTERNAL":
            # if ifc_space_boundary.CorrespondingBoundary is None:
              # os_surface.setOutsideBoundaryCondition("Adiabatic")
            # elif ifc_space_boundary.CorrespondingBoundary in ifc2os:
              # os_surface.setAdjacentSurface(ifc2os[ifc_space_boundary.CorrespondingBoundary])
          # else:
            # os_surface.setOutsideBoundaryCondition("Outdoors")
          # ifc_building_element = ifc_space_boundary.RelatedBuildingElement
          # ifc_rel_associates = ifc_building_element.HasAssociations
          # if ifc_building_element.IsTypedBy:
            # ifc_rel_associates = ifc_building_element.IsTypedBy[0].RelatingType.HasAssociations
          # ifc_rel_associates_material = next((x for x in ifc_rel_associates if x.is_a("IfcRelAssociatesMaterial")), None)
          # if ifc_rel_associates_material is not None:
            # os_surface.setConstruction(ifc2os[ifc_rel_associates_material.RelatingMaterial])
          # ifc2os[ifc_space_boundary] = os_surface

          # for ifc_inner_boundary in ifc_space_boundary.InnerBoundaries:
            # if ifc_inner_boundary.ParentBoundary != ifc_space_boundary:
              # continue

            # os_sub_surface = openstudio.model.SubSurface(getVertices(ifc_inner_boundary, space_matrix), model)
            # os_sub_surface.setName(ifc_inner_boundary.Name)
            # os_sub_surface.setSurface(os_surface)
            # if (ifc_inner_boundary.InternalOrExternalBoundary == "INTERNAL" and
              # ifc_inner_boundary.CorrespondingBoundary is not None and
              # ifc_inner_boundary.CorrespondingBoundary in ifc2os):
              # os_sub_surface.setAdjacentSubSurface(ifc2os[ifc_inner_boundary.CorrespondingBoundary])
            # ifc2os[ifc_inner_boundary] = os_sub_surface

    # model.save(openstudio.toPath("C:/BIM2BEM/output.osm"), True)

    print("FIN")






def processItem(item):
    model = item[0]
    filePath = item[1]
	# Make sure the file extension is .OSM
    ext = filePath[len(filePath)-4:len(filePath)]
    if ext.lower() != ".osm":
        filePath = filePath+".osm"
    osCondition = False
    osPath = openstudio.openstudioutilitiescore.toPath(filePath)
    osCondition = model.save(osPath, True)
    return osCondition

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]


class SvEnergyModelIFCToOSM(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Exports the input Energy Model to an OSM file   
	"""
	bl_idname = 'SvEnergyModelExportToOSM'
	bl_label = 'EnergyModel.ExportToOSM'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Energy Model')
		self.inputs.new('SvStringsSocket', 'File Path')
		self.outputs.new('SvStringsSocket', 'Status')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Status'].sv_set([False])
			return
		modelList = self.inputs['Energy Model'].sv_get(deepcopy=True)
		modelList = flatten(modelList)
		filePathList = self.inputs['File Path'].sv_get(deepcopy=True)
		filePathList = flatten(filePathList)
		inputs = [modelList, filePathList]
		if ((self.Replication) == "Default"):
			inputs = iterate(inputs)
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
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Status'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEnergyModelExportToOSM)

def unregister():
	bpy.utils.unregister_class(SvEnergyModelExportToOSM)
