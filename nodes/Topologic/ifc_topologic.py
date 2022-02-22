
import ifcopenshell
from . import topologic_lib
import topologic
import numpy as np
import openstudio

def getIfcSettings():
  settings = ifcopenshell.geom.settings()
  settings.set(settings.USE_BREP_DATA, True)
  settings.set(settings.SEW_SHELLS, True)
  settings.set(settings.USE_WORLD_COORDS, True)
  settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)

  return settings

def getIfcProductCell(product):
  shape = ifcopenshell.geom.create_shape(getIfcSettings(), product)
  brepString = shape.geometry.brep_data
  topology = topologic.Topology.ByString(brepString)
  faces = topologic_lib.getSubTopologies(topology, topologic.Face)

  return topologic.Cell.ByFaces(faces, 1e-4)

def createIfcFaceSurface(ifc_file, element_matrix, vertices, face):
  element_vertices = [np.linalg.solve(element_matrix, np.array(v+(1,)))[:-1] for v in vertices]

  p = element_vertices[face[0]]
  u = topologic_lib.normalize(element_vertices[face[1]] - p)
  v = element_vertices[face[-1]] - p
  n = topologic_lib.normalize(np.cross(u, v))
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

def getFacesStorey(faces, ifc_file):
  ifc_faces_storey, elevation = None, None

  for face in faces:
    ifc_building_element = ifc_file.by_guid(topologic_lib.getDictionary(face, "IfcBuildingElement"))
    # if not ifc_building_element.is_a("IfcSlab"):
      # continue

    if not ifc_building_element.ContainedInStructure:
      ifc_building_element = ifc_building_element.Decomposes[0].RelatingObject
    ifc_storey = ifc_building_element.ContainedInStructure[0].RelatingStructure

    if elevation is None or ifc_storey.Elevation < elevation:
      ifc_faces_storey, elevation = ifc_storey, ifc_storey.Elevation

  return ifc_faces_storey

def assignRepresentation(topology, ifc_file, ifc_product):
  vs, fs = topologic_lib.meshData(topology)
  o, z = None, None
  for v in vs:
    if z is None or v[-1] < z:
      o, z = v, v[-1]

  product_matrix = ifcopenshell.util.placement.a2p(o, np.array([0,0,1]), np.array([1,0,0]))
  point_list = ifc_file.createIfcCartesianPointList3D([ np.linalg.solve(product_matrix, np.append(v,1))[:-1].tolist() for v in vs ])
  indexed_faces = [ ifc_file.createIfcIndexedPolygonalFace([ index + 1 for index in f]) for f in fs ]
  representation = ifc_file.createIfcPolygonalFaceSet(point_list, None, indexed_faces, None)
  body_context = next((item  for item  in ifc_file.by_type("IfcGeometricRepresentationSubContext") if item.ContextIdentifier == "Body"), None)
  shape = ifc_file.createIfcShapeRepresentation(body_context, body_context.ContextIdentifier, "Tessellation", [representation])

  ifcopenshell.api.run("geometry.assign_representation", ifc_file, product=ifc_product, representation=shape)
  ifcopenshell.api.run("geometry.edit_object_placement", ifc_file, product=ifc_product, matrix=product_matrix)

  return True

def createRelSpaceBoundary(ifc_file, ifc_class, description, ifc_space, ifc_building_element, vertices, f, boundary_condition):
  ifc_rel_space_boundary = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class=ifc_class)
  ifc_rel_space_boundary.Name = "Boundary " + str(len(ifc_file.by_type("IfcRelSpaceBoundary")) - 1)
  if description is not None:
    ifc_rel_space_boundary.Description = description
  ifc_rel_space_boundary.RelatingSpace = ifc_space
  ifc_rel_space_boundary.RelatedBuildingElement = ifc_building_element
  ifc_rel_space_boundary.ConnectionGeometry = createConnectionSurfaceGeometry(ifc_file, ifc_space, ifc_building_element, vertices, f)
  ifc_rel_space_boundary.PhysicalOrVirtualBoundary = "PHYSICAL"
  ifc_rel_space_boundary.InternalOrExternalBoundary = boundary_condition

  return ifc_rel_space_boundary

def createRelSpaceBoundary2ndLevel(ifc_file, top_space_boundary, reverse, ifc_space, other_ifc_space, ifc_building_element, space_boundary_2b):
  ifc_rel_space_boundary = None
  if ifc_space is not None:
    vs, fs = topologic_lib.meshData(top_space_boundary)
    f = fs[0][::-1] if reverse else fs[0]
    boundary_condition = "EXTERNAL" if other_ifc_space is None else "INTERNAL"
    ifc_rel_space_boundary = createRelSpaceBoundary(ifc_file, "IfcRelSpaceBoundary2ndLevel", "2a", ifc_space, ifc_building_element, vs, f, boundary_condition)
    space_boundary_2b = topologic_lib.boolean(space_boundary_2b, top_space_boundary, "Difference")

  return [ifc_rel_space_boundary, space_boundary_2b]

def createInnerBoundary(ifc_rel_space_boundary, top_opening_element, top_space_boundary, reverse, ifc_file):
  if ifc_rel_space_boundary is None:
    return None

  top_inner_boundary = topologic_lib.boolean(top_space_boundary, top_opening_element, "Intersect")
  if top_inner_boundary is None:
    return None

  vs, fs = topologic_lib.meshData(top_inner_boundary)
  if not fs:
    return None
  f = fs[0][::-1] if reverse else fs[0]

  ifc_element = ifc_file.by_guid(topologic_lib.getDictionary(top_opening_element, "IfcElement"))
  ifc_space = ifc_rel_space_boundary.RelatingSpace
  boundary_condition = ifc_rel_space_boundary.InternalOrExternalBoundary
  ifc_inner_boundary = createRelSpaceBoundary(ifc_file, "IfcRelSpaceBoundary2ndLevel", "2a", ifc_space, ifc_element, vs, f, boundary_condition)
  ifc_inner_boundary.ParentBoundary = ifc_rel_space_boundary

  return ifc_inner_boundary

def getOpenStudioVertices(ifc_rel_space_boundary):
  ifc_curve = ifc_rel_space_boundary.ConnectionGeometry.SurfaceOnRelatingElement
  if ifc_curve.is_a('IfcFaceSurface'):
    ifc_points = ifc_curve.Bounds[0].Bound.Polygon
    ifc_plane = ifc_curve.FaceSurface
  elif ifc_curve.is_a('IfcCurveBoundedPlane'):
    ifc_points = ifc_curve.OuterBoundary.Points
    ifc_plane = ifc_curve.BasisSurface
  plane_vertices = [ v.Coordinates for v in ifc_points ]
  plane_matrix = ifcopenshell.util.placement.get_axis2placement(ifc_plane.Position)
  vertices = [ (plane_matrix @ np.array(v+(0,1))) for v in plane_vertices ]

  return [ openstudio.Point3d(v[0], v[1], v[2]) for v in vertices ]