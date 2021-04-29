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
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	_ = cell.Vertices(vertices)
	x = []
	y = []
	z = []
	for aVertex in vertices:
		x.append(aVertex.X())
		y.append(aVertex.Y())
		z.append(aVertex.Z())
	return ([min(x), min(y), min(z), max(x), max(y), max(z)])

def isInside(aperture, face, tolerance):
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	_ = aperture.Vertices(vertices)
	for vertex in vertices:
		if topologic.FaceUtility.IsInside(face, vertex, tolerance) == False:
			return False
	return True
	
def processItem(faces, apertures, exclusive, tolerance):
	usedFaces = []
	for face in faces:
			usedFaces.append(0)
	for aperture in apertures:
		apCenter = topologic.FaceUtility.InternalVertex(aperture)
		for i in range(len(faces)):
			face = faces[i]
			if exclusive == True and usedFaces[i] == 1:
				continue
			if topologic.VertexUtility.Distance(apCenter, face) < tolerance:
				context = topologic.Context.ByTopologyParameters(face, 0.5, 0.5, 0.5)
				_ = topologic.Aperture.ByTopologyContext(aperture, context)
				if exclusive == True:
					usedFaces[i] = 1
	return faces

class SvFaceAddAperture(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Adds the input Aperture to the input Face
	"""
	bl_idname = 'SvFaceAddAperture'
	bl_label = 'Face.AddAperture'
	Exclusive: BoolProperty(name="Exclusive", default=True, update=updateNode)
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)


	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'Aperture')
		self.inputs.new('SvStringsSocket', 'Exclusive').prop_name = 'Exclusive'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return

		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		apertureList = self.inputs['Aperture'].sv_get(deepcopy=False)
		exclusive = self.inputs['Exclusive'].sv_get(deepcopy=False)[0][0]
		tolerance = self.inputs['Tolerance'].sv_get(deepcopy=False)[0][0]

		output = processItem(faceList, apertureList, exclusive, tolerance)
		end = time.time()
		print("Face Add Aperture Operation consumed "+str(round(end - start,4))+" seconds")
		self.outputs['Face'].sv_set(output)

def register():
	bpy.utils.register_class(SvFaceAddAperture)

def unregister():
	bpy.utils.unregister_class(SvFaceAddAperture)
