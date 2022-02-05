
import topologic
import numpy as np

def getSubTopologies(topology, subTopologyClass):
  subtopologies = []

  if topology is None or topology.Type() < subTopologyClass.Type():
    return subtopologies

  if subTopologyClass == topologic.Vertex:
    _ = topology.Vertices(None, subtopologies)
  if subTopologyClass == topologic.Edge:
    _ = topology.Edges(None, subtopologies)
  elif subTopologyClass == topologic.Face:
    _ = topology.Faces(None, subtopologies)
  elif subTopologyClass == topologic.Cell:
    _ = topology.Cells(None, subtopologies)

  return subtopologies

def boolean(topologyA, topologyB, operation):
  topologyC = None

  try:
    if operation == "Difference":
      topologyC = topologyA.Difference(topologyB, False)
    elif operation == "Intersect":
      topologyC = topologyA.Intersect(topologyB, False)

    if not topologyC:
      return None
  except:
    return None

  return topologyC

def setDictionary(elem, key, value):
  dictionary = elem.GetDictionary()
  dictionary.TryAdd(key, topologic.StringAttribute(value))
  elem.SetDictionary(dictionary)

def getDictionary(elem, key):
  dictionary = elem.GetDictionary()
  if dictionary.ContainsKey(key):
    value = dictionary.ValueAtKey(key)
    return value.StringValue()

  return None

def getBoundingBox(cell):
  x = []
  y = []
  z = []
  for vertex in getSubTopologies(cell, topologic.Vertex):
    x.append(vertex.X())
    y.append(vertex.Y())
    z.append(vertex.Z())
  x.sort()
  y.sort()
  z.sort()

  return topologic.EdgeUtility.ByVertices([topologic.Vertex.ByCoordinates(x[0], y[0], z[0]), topologic.Vertex.ByCoordinates(x[-1], y[-1], z[-1])])

def doBoundingBoxIntersect(bounding_box, other_bounding_box):
  if bounding_box.EndVertex().X() < other_bounding_box.StartVertex().X() - 1e-2 or other_bounding_box.EndVertex().X() < bounding_box.StartVertex().X() - 1e-2:
    return False

  if bounding_box.EndVertex().Y() < other_bounding_box.StartVertex().Y() - 1e-2 or other_bounding_box.EndVertex().Y() < bounding_box.StartVertex().Y() - 1e-2:
    return False

  if bounding_box.EndVertex().Z() < other_bounding_box.StartVertex().Z() - 1e-2 or other_bounding_box.EndVertex().Z() < bounding_box.StartVertex().Z() - 1e-2:
    return False

  return True

def normalize(u):
  return u / np.linalg.norm(u)

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
      for aVertex in getSubTopologies(topologic.WireUtility.RemoveCollinearEdges(wire, 0.1), topologic.Vertex):
        try:
          fVertexIndex = vertices.index(tuple([aVertex.X(), aVertex.Y(), aVertex.Z()]))
        except:
          vertices.append(tuple([aVertex.X(), aVertex.Y(), aVertex.Z()]))
          fVertexIndex = len(vertices)-1
        f.append(fVertexIndex)

      p = np.array(vertices[f[0]])
      u = normalize(np.array(vertices[f[1]] - p))
      v = np.array(vertices[f[-1]]) - p
      normal = topologic.FaceUtility.NormalAtParameters(aFace, 0.5, 0.5)
      if normalize(np.cross(u, v)) @ np.array([normal[0], normal[1], normal[2]]) + 1 < 1e-6:
        f.reverse()

      faces.append(tuple(f))

  return [vertices, faces]