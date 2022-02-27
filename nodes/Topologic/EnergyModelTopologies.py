import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
try:
	import openstudio
except:
	raise Exception("Error: Could not import openstudio.")

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
    surfaceEdges = []
    surfaceVertices = surface.vertices()
    for i in range(len(surfaceVertices)-1):
        sv = topologic.Vertex.ByCoordinates(surfaceVertices[i].x(), surfaceVertices[i].y(), surfaceVertices[i].z())
        ev = topologic.Vertex.ByCoordinates(surfaceVertices[i+1].x(), surfaceVertices[i+1].y(), surfaceVertices[i+1].z())
        edge = topologic.Edge.ByStartVertexEndVertex(sv, ev)
        surfaceEdges.append(edge)
    sv = topologic.Vertex.ByCoordinates(surfaceVertices[len(surfaceVertices)-1].x(), surfaceVertices[len(surfaceVertices)-1].y(), surfaceVertices[len(surfaceVertices)-1].z())
    ev = topologic.Vertex.ByCoordinates(surfaceVertices[0].x(), surfaceVertices[0].y(), surfaceVertices[0].z())
    edge = topologic.Edge.ByStartVertexEndVertex(sv, ev)
    surfaceEdges.append(edge)
    surfaceWire = topologic.Wire.ByEdges(surfaceEdges)
    internalBoundaries = []
    surfaceFace = topologic.Face.ByExternalInternalBoundaries(surfaceWire, internalBoundaries)
    return surfaceFace

def addApertures(face, apertures):
	usedFaces = []
	for aperture in apertures:
		cen = aperture.CenterOfMass()
		try:
			params = face.ParametersAtVertex(cen)
			u = params[0]
			v = params[1]
			w = 0.5
		except:
			u = 0.5
			v = 0.5
			w = 0.5
		context = topologic.Context.ByTopologyParameters(face, u, v, w)
		_ = topologic.Aperture.ByTopologyContext(aperture, context)
	return face

def processItem(item):
    spaces = item.getSpaces()
    vertexIndex = 0
    cells = []
    apertures = []
    shadingFaces = []
    shadingSurfaces = item.getShadingSurfaces()
    for aShadingSurface in shadingSurfaces:
        shadingFaces.append(surfaceToFace(aShadingSurface))
    for count, aSpace in enumerate(spaces):
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
        spaceFaces = []
        surfaces = aSpace.surfaces()
        for aSurface in surfaces:
            aFace = surfaceToFace(aSurface)
            aFace = topologic.TopologyUtility.Transform(aFace, osTranslation.x(), osTranslation.y(), osTranslation.z(), rotation11, rotation12, rotation13, rotation21, rotation22, rotation23, rotation31, rotation32, rotation33)
            #aFace.__class__ = topologic.Face
            subSurfaces = aSurface.subSurfaces()
            for aSubSurface in subSurfaces:
                aperture = surfaceToFace(aSubSurface)
                aperture = topologic.TopologyUtility.Transform(aperture, osTranslation.x(), osTranslation.y(), osTranslation.z(), rotation11, rotation12, rotation13, rotation21, rotation22, rotation23, rotation31, rotation32, rotation33)
                # aperture.__class__ = topologic.Face
                apertures.append(aperture)
            addApertures(aFace, apertures)
            spaceFaces.append(aFace)
        spaceCell = topologic.Cell.ByFaces(spaceFaces)
        print(count, spaceCell)
        if not spaceCell:
            spaceCell = topologic.Shell.ByFaces(spaceFaces)
        if not spaceCell:
            spaceCell = topologic.Cluster.ByTopologies(spaceFaces)
        if spaceCell:
            # Set Dictionary for Cell
            stl_keys = []
            stl_keys.append("TOPOLOGIC_id")
            stl_keys.append("TOPOLOGIC_name")
            stl_keys.append("TOPOLOGIC_type")
            stl_keys.append("TOPOLOGIC_color")
            stl_values = []
            spaceID = str(aSpace.handle()).replace('{','').replace('}','')
            stl_values.append(topologic.StringAttribute(spaceID))
            stl_values.append(topologic.StringAttribute(aSpace.name().get()))
            spaceTypeName = "Unknown"
            red = 255
            green = 255
            blue = 255
            if (aSpace.spaceType().is_initialized()):
                if(aSpace.spaceType().get().name().is_initialized()):
                    spaceTypeName = aSpace.spaceType().get().name().get()
                if(aSpace.spaceType().get().renderingColor()):
                    red = aSpace.spaceType().get().renderingColor().get().renderingRedValue()
                    green = aSpace.spaceType().get().renderingColor().get().renderingGreenValue()
                    blue = aSpace.spaceType().get().renderingColor().get().renderingBlueValue()
            stl_values.append(topologic.StringAttribute(spaceTypeName))
            l = []
            l.append(topologic.IntAttribute(red))
            l.append(topologic.IntAttribute(green))
            l.append(topologic.IntAttribute(blue))
            stl_values.append(topologic.ListAttribute(l))
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
		self.outputs.new('SvStringsSocket', 'Topologies')
		self.outputs.new('SvStringsSocket', 'Apertures')
		self.outputs.new('SvStringsSocket', 'Shading Faces')
	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topologies'].sv_set([])
			self.outputs['Apertures'].sv_set([])
			return
		inputs = self.inputs['Energy Model'].sv_get(deepcopy=True)
		inputs = flatten(inputs)
		cellOutputs = []
		apertureOutputs = []
		shadingFaceOutputs = []
		for anInput in inputs:
			cells, apertures, shadingFaces = processItem(anInput)
			cellOutputs.append(cells)
			apertureOutputs.append(apertures)
			shadingFaceOutputs.append(shadingFaces)
		self.outputs['Topologies'].sv_set(cellOutputs)
		self.outputs['Apertures'].sv_set(apertureOutputs)
		self.outputs['Shading Faces'].sv_set(shadingFaceOutputs)

def register():
	bpy.utils.register_class(SvEnergyModelTopologies)

def unregister():
	bpy.utils.unregister_class(SvEnergyModelTopologies)
