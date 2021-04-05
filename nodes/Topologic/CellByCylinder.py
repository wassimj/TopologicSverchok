import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
import cppyy
import math

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

def wireByVertices(vList):
	edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
	for i in range(len(vList)-1):
		edges.push_back(topologic.Edge.ByStartVertexEndVertex(vList[i], vList[i+1]))
	edges.push_back(topologic.Edge.ByStartVertexEndVertex(vList[-1], vList[0]))
	return topologic.Wire.ByEdges(edges)

def processItem(item, originLocation):
	origin = item[0]
	radius = item[1]
	height = item[2]
	sides = item[3]
	baseV = []
	topV = []
	xOffset = 0
	yOffset = 0
	zOffset = 0
	if originLocation == "Center":
		zOffset = -height*0.5
	elif originLocation == "LowerLeft":
		xOffset = radius*0.5
		yOffset = radius*0.5

	for i in range(sides):
		angle = math.radians(360/sides)*i
		x = math.sin(angle)*radius + origin.X() + xOffset
		y = math.cos(angle)*radius + origin.Y() + yOffset
		z = origin.Z() + zOffset
		baseV.append(topologic.Vertex.ByCoordinates(x,y,z))
		topV.append(topologic.Vertex.ByCoordinates(x,y,z+height))

	baseWire = wireByVertices(baseV)
	topWire = wireByVertices(topV)
	wires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	wires.push_back(baseWire)
	wires.push_back(topWire)
	return topologic.CellUtility.ByLoft(wires)

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

originLocations = [("Bottom", "Bottom", "", 1),("Center", "Center", "", 2),("LowerLeft", "LowerLeft", "", 3)]

class SvCellByCylinder(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cell from the input cylinder parameters    
	"""
	bl_idname = 'SvCellByCylinder'
	bl_label = 'Cell.ByCylinder'
	Radius: FloatProperty(name="Radius", default=1, min=0.0001, precision=4, update=updateNode)
	Height: FloatProperty(name="Height", default=1, min=0.0001, precision=4, update=updateNode)
	Sides: IntProperty(name="Sides", default=16, min=3, max=360, update=updateNode)
	originLocation: EnumProperty(name="originLocation", description="Specify origin location", default="Bottom", items=originLocations, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'Radius'
		self.inputs.new('SvStringsSocket', 'Height').prop_name = 'Height'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'Sides'
		self.outputs.new('SvStringsSocket', 'Cell')

	def draw_buttons(self, context, layout):
		layout.prop(self, "originLocation",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		originList = self.inputs['Origin'].sv_get(deepcopy=False)
		radiusList = self.inputs['Radius'].sv_get(deepcopy=False)[0]
		heightList = self.inputs['Height'].sv_get(deepcopy=False)[0]
		sidesList = self.inputs['Sides'].sv_get(deepcopy=False)[0]
		matchLengths([originList, radiusList, heightList, sidesList])
		newInputs = zip(originList, radiusList, heightList, sidesList)
		outputs = []
		for anInput in newInputs:
			outputs.append(processItem(anInput, self.originLocation))
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellByCylinder)

def unregister():
	bpy.utils.unregister_class(SvCellByCylinder)
