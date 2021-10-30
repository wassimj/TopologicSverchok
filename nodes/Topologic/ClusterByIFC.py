import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import sys
sys.path.append("C:\\ProgramData\\Anaconda3\\envs\\Blender377\\Lib\\site-packages")
import ifcopenshell
import ifcopenshell.geom
import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph, Dictionary, Attribute, AttributeManager, VertexUtility, EdgeUtility, WireUtility, ShellUtility, CellUtility, TopologyUtility

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def edgesByVertices(vertices):
	edges = []

	edges = cppyy.gbl.std.list[Edge.Ptr]()
	for i in range(len(vertices)-1):
		v1 = vertices[i]
		v2 = vertices[i+1]
		e1 = Edge.ByStartVertexEndVertex(v1, v2)
		edges.push_back(e1)

	# connect the last vertex to the first one
	v1 = vertices[len(vertices)-1]
	v2 = vertices[0]
	e1 = Edge.ByStartVertexEndVertex(v1, v2)
	edges.push_back(e1)
	return edges

def processItem(item, tol):
	settings = ifcopenshell.geom.settings()
	settings.set(settings.USE_BREP_DATA,True)
	settings.set(settings.SEW_SHELLS,True)
	settings.set(settings.USE_WORLD_COORDS,True)

	ifc_file = ifcopenshell.open(item)
	products = ifc_file.by_type('IfcProduct')
	output = []
	for p in products:
		try:
			cr = ifcopenshell.geom.create_shape(settings, p)
			brep = cr.geometry.brep_data
			output.append(brep)
		except:
			continue
	return output

'''
def processItem(item, tol):
	print(item)
	settings = ifcopenshell.geom.settings()
	settings.set(settings.USE_WORLD_COORDS, True)
	ifc_file = ifcopenshell.open(item)
	build_elem_ccs = []
	build_cc = None
	for building_element in ifc_file.by_type('IfcBuildingElement'):
		if not (building_element.is_a('IfcWall') or building_element.is_a('IfcSlab')):
			continue
		shape = ifcopenshell.geom.create_shape(settings, building_element)
		geo = shape.geometry
		geo_vertices = geo.verts
		geo_faces = geo.faces
		topo_vertices = []
		for v in range(0, len(geo_vertices), 3):
			vertex = Vertex.ByCoordinates(geo_vertices[v], geo_vertices[v+1], geo_vertices[v+2])
			topo_vertices.append(vertex)
		topo_faces = cppyy.gbl.std.list[Face.Ptr]()
		for f in range(0, len(geo_faces), 3):
			face_vertices = []
			for v in geo_faces[f : f + 3]:
				vertex = topo_vertices[v]
				face_vertices.append(vertex)
			edges = edgesByVertices(face_vertices)
			face = Face.ByEdges(edges)
			topo_faces.push_back(face)
	cc = CellComplex.ByFaces(topo_faces, tol)
	build_elem_ccs.append(cc)
	if build_cc is None:
		build_cc = cc
	else:
		build_cc = Topology.Merge(build_cc, cc)
	return build_cc
'''
def recur(input, tol):
	output = []
	if input == None:
		return []
	if isinstance(input[0], list):
		for anItem in input:
			output.append(recur(anItem, tol))
	else:
		output = processItem(input, tol)
	return output

class SvCellComplexByIFC(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a CellComplex from an IFC file  
	"""
	bl_idname = 'SvCellComplexByIFC'
	bl_label = 'CellComplex.ByIFC'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'IFC File Path')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'CellComplex')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['IFC File Path'].sv_get(deepcopy=False)[0]
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0][0]
		cellComplexes = recur(inputs, tol)
		self.outputs['CellComplex'].sv_set(flatten(cellComplexes))

def register():
    bpy.utils.register_class(SvCellComplexByIFC)

def unregister():
    bpy.utils.unregister_class(SvCellComplexByIFC)
