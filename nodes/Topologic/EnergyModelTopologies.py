import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import cppyy
import openstudio

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def surfaceToFace(surface):
    surfaceEdges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
    surfaceIndices = cppyy.gbl.std.list[int]()
    surfaceVertices = surface.vertices()
    for i in range(len(surfaceVertices)-1):
        sv = topologic.Vertex.ByCoordinates(surfaceVertices[i].x(), surfaceVertices[i].y(), surfaceVertices[i].z())
        ev = topologic.Vertex.ByCoordinates(surfaceVertices[i+1].x(), surfaceVertices[i+1].y(), surfaceVertices[i+1].z())
        edge = topologic.Edge.ByStartVertexEndVertex(sv, ev)
        surfaceEdges.push_back(edge)
    sv = topologic.Vertex.ByCoordinates(surfaceVertices[len(surfaceVertices)-1].x(), surfaceVertices[len(surfaceVertices)-1].y(), surfaceVertices[len(surfaceVertices)-1].z())
    ev = topologic.Vertex.ByCoordinates(surfaceVertices[0].x(), surfaceVertices[0].y(), surfaceVertices[0].z())
    edge = topologic.Edge.ByStartVertexEndVertex(sv, ev)
    surfaceEdges.push_back(edge)
    surfaceWire = topologic.Wire.ByEdges(surfaceEdges)
    internalBoundaries = cppyy.gbl.std.list[topologic.Wire.Ptr]()
    surfaceFace = topologic.Face.ByExternalInternalBoundaries(surfaceWire, internalBoundaries)
    return surfaceFace

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
    spaces = item.getSpaces()
    vertexIndex = 0
    cells = []
    apertures = cppyy.gbl.std.list[topologic.Face.Ptr]()
    shadingFaces = []
    shadingSurfaces = item.getShadingSurfaces()
    for aShadingSurface in shadingSurfaces:
        shadingFaces.append(surfaceToFace(aShadingSurface))
    for aSpace in spaces:
        osTransformation = aSpace.transformation()
        osTranslation = osTransformation.translation()
        osMatrix = osTransformation.rotationMatrix()
        rotation11 = osMatrix[0, 0]
        rotation12 = osMatrix[0, 1]
        rotation13 = osMatrix[0, 2]
        rotation21 = osMatrix[1, 0]
        rotation22 = osMatrix[1, 1]
        rotation23 = osMatrix[1, 2]
        rotation31 = osMatrix[2, 0]
        rotation32 = osMatrix[2, 1]
        rotation33 = osMatrix[2, 2]
        spaceFaces = cppyy.gbl.std.list[topologic.Face.Ptr]()
        surfaces = aSpace.surfaces()
        for aSurface in surfaces:
            aFace = surfaceToFace(aSurface)
            aFace = topologic.TopologyUtility.Transform(aFace, osTranslation.x(), osTranslation.y(), osTranslation.z(), rotation11, rotation12, rotation13, rotation21, rotation22, rotation23, rotation31, rotation32, rotation33)
            aFace.__class__ = topologic.Face
            subSurfaces = aSurface.subSurfaces()
            for aSubSurface in subSurfaces:
                aperture = surfaceToFace(aSubSurface)
                aperture = topologic.TopologyUtility.Transform(aperture, osTranslation.x(), osTranslation.y(), osTranslation.z(), rotation11, rotation12, rotation13, rotation21, rotation22, rotation23, rotation31, rotation32, rotation33)
                aperture.__class__ = topologic.Face
                apertures.push_back(aperture)
            aFace.AddApertures(apertures)
            spaceFaces.push_back(aFace)
        spaceCell = topologic.Cell.ByFaces(spaceFaces)
        # Set Dictionary for Cell
        stl_keys = cppyy.gbl.std.list[cppyy.gbl.std.string]()
        stl_keys.push_back("id")
        stl_keys.push_back("name")
        stl_keys.push_back("type")
        stl_keys.push_back("color")
        stl_values = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
        spaceID = str(aSpace.handle()).replace('{','').replace('}','')
        stl_values.push_back(topologic.StringAttribute(spaceID))
        stl_values.push_back(topologic.StringAttribute(aSpace.name().get()))
        spaceTypeName = "Unknown"
        try:
            spaceTypeName = aSpace.spaceType().get().name().get()
        except:
            spaceTypeName = "Unknown"
        stl_values.push_back(topologic.StringAttribute(spaceTypeName))
        try:
            red = aSpace.spaceType().get().renderingColor().get().renderingRedValue()
            green = aSpace.spaceType().get().renderingColor().get().renderingGreenValue()
            blue = aSpace.spaceType().get().renderingColor().get().renderingBlueValue()
        except:
            red = 255
            green = 255
            blue = 255
        l = cppyy.gbl.std.list[topologic.Attribute.Ptr]()
        l.push_back(topologic.IntAttribute(red))
        l.push_back(topologic.IntAttribute(green))
        l.push_back(topologic.IntAttribute(blue))
        stl_values.push_back(topologic.ListAttribute(l))
        dict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
        _ = spaceCell.SetDictionary(dict)
        cells.append(spaceCell)
    return [cells, apertures, shadingFaces]
		
class SvEnergyModelTopologies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Returns the Topologies found in the input Energy Model
	"""
	bl_idname = 'SvEnergyModelTopologies'
	bl_label = 'EnergyModel.Topologies'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Energy Model')
		self.outputs.new('SvStringsSocket', 'Cells')
		self.outputs.new('SvStringsSocket', 'Apertures')
		self.outputs.new('SvStringsSocket', 'Shading Faces')
	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Cells'].sv_set([])
			self.outputs['Apertures'].sv_set([])
			return
		inputs = self.inputs['Energy Model'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		cellOutputs = []
		apertureOutputs = []
		shadingFaceOutputs = []
		for anInput in inputs:
			cells, apertures, shadingFaces = processItem(anInput)
			cellOutputs.append(cells)
			apertureOutputs.append(apertures)
			shadingFaceOutputs.append(shadingFaces)
		self.outputs['Cells'].sv_set(cellOutputs)
		self.outputs['Apertures'].sv_set(apertureOutputs)
		self.outputs['Shading Faces'].sv_set(shadingFaceOutputs)

def register():
	bpy.utils.register_class(SvEnergyModelTopologies)

def unregister():
	bpy.utils.unregister_class(SvEnergyModelTopologies)
