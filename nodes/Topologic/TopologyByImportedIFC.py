import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import sys
try:
	import ifcopenshell
	import ifcopenshell.geom
except:
	raise Exception("Error: TopologyByImportedIFC: ifcopenshell is not present on your system. Install BlenderBIM or ifcopenshell to resolve.")
import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import uuid

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processKeysValues(keys, values):
	if len(keys) != len(values):
		raise Exception("DictionaryByKeysValues - Keys and Values do not have the same length")
	stl_keys = []
	stl_values = []
	for i in range(len(keys)):
		if isinstance(keys[i], str):
			stl_keys.append(keys[i])
		else:
			stl_keys.append(str(keys[i]))
		if isinstance(values[i], list) and len(values[i]) == 1:
			value = values[i][0]
		else:
			value = values[i]
		if isinstance(value, bool):
			if value == False:
				stl_values.append(topologic.IntAttribute(0))
			else:
				stl_values.append(topologic.IntAttribute(1))
		elif isinstance(value, int):
			stl_values.append(topologic.IntAttribute(value))
		elif isinstance(value, float):
			stl_values.append(topologic.DoubleAttribute(value))
		elif isinstance(value, str):
			stl_values.append(topologic.StringAttribute(value))
		elif isinstance(value, list):
			l = []
			for v in value:
				if isinstance(v, bool):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, int):
					l.append(topologic.IntAttribute(v))
				elif isinstance(v, float):
					l.append(topologic.DoubleAttribute(v))
				elif isinstance(v, str):
					l.append(topologic.StringAttribute(v))
			stl_values.append(topologic.ListAttribute(l))
		else:
			raise Exception("Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
	myDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
	return myDict

def triangulate(faces):
	triangles = []
	for aFace in faces:
		ib = []
		_ = aFace.InternalBoundaries(ib)
		if len(ib) != 0:
			print("Found Internal Boundaries")
			faceTriangles = []
			topologic.FaceUtility.Triangulate(aFace, 0.0, faceTriangles)
			print("Length of Face Triangles:", len(faceTriangles))
			for aFaceTriangle in faceTriangles:
				triangles.append(aFaceTriangle)
		else:
			triangles.append(aFace)
	return triangles

def processItem(filePath, typeList):
	settings = ifcopenshell.geom.settings()
	settings.set(settings.USE_BREP_DATA,True)
	settings.set(settings.SEW_SHELLS,True)
	settings.set(settings.USE_WORLD_COORDS,False)

	ifc_file = ifcopenshell.open(filePath)
	if len(typeList) < 1:
		typeList = ifc_file.types()
	returnList = []
	for aType in typeList:
		products = ifc_file.by_type(aType)
		for p in products:
			try:
				cr = ifcopenshell.geom.create_shape(settings, p)
				brepString = cr.geometry.brep_data
				topology = topologic.Topology.ByString(brepString)
				if topology.Type() == 8:
					triangles = triangulate([topology])
					topology = topologic.Cluster.ByTopologies(triangles)
				elif topology.Type() > 8:
					faces = []
					_ = topology.Faces(None, faces)
					triangles = triangulate(faces)
					topology = topologic.Cluster.ByTopologies(triangles)
				keys = []
				values = []
				keys.append("TOPOLOGIC_color")
				values.append([1.0,1.0,1.0,1.0])
				keys.append("TOPOLOGIC_id")
				values.append(str(uuid.uuid4()))
				keys.append("TOPOLOGIC_name")
				values.append(p.Name)
				keys.append("TOPOLOGIC_type")
				values.append(topology.GetTypeAsString())
				keys.append("IFC_id")
				values.append(str(p.GlobalId))
				keys.append("IFC_name")
				values.append(p.Name)
				keys.append("IFC_type")
				values.append(p.is_a())
				for definition in p.IsDefinedBy:
					# To support IFC2X3, we need to filter our results.
					if definition.is_a('IfcRelDefinesByProperties'):
						property_set = definition.RelatingPropertyDefinition
						for property in property_set.HasProperties:
							if property.is_a('IfcPropertySingleValue'):
								keys.append(property.Name)
								values.append(property.NominalValue.wrappedValue)
				topDict = processKeysValues(keys, values)
				_ = topology.SetDictionary(topDict)
			except:
				continue
			returnList.append(topology)
	return returnList

class SvTopologyByImportedIFC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology from the input IFC file 
	"""
	bl_idname = 'SvTopologyByImportedIFC'
	bl_label = 'Topology.ByImportedIFC'
	FilePath: StringProperty(name="file", default="", subtype="FILE_PATH")

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'File Path').prop_name='FilePath'
		self.inputs.new('SvStringsSocket', 'IFC Types')
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		filePath = self.inputs['File Path'].sv_get(deepcopy=False)[0]
		if not (self.inputs['IFC Types'].is_linked):
			typeList = ['ifcProduct']
		else:
			typeList = self.inputs['IFC Types'].sv_get(deepcopy=False)
			typeList = flatten(typeList)
		outputs = []
		outputs.append(processItem(filePath, typeList))
		outputs = flatten(outputs)
		self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvTopologyByImportedIFC)

def unregister():
    bpy.utils.unregister_class(SvTopologyByImportedIFC)
