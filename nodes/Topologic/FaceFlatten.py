import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import math

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	origin = topologic.Vertex.ByCoordinates(0,0,0)
	cm = item.CenterOfMass()
	coords = topologic.FaceUtility.NormalAtParameters(item, 0.5, 0.5)
	x1 = cm.X()
	y1 = cm.Y()
	z1 = cm.Z()
	x2 = cm.X() + coords[0]
	y2 = cm.Y() + coords[1]
	z2 = cm.Z() + coords[2]
	dx = x2 - x1
	dy = y2 - y1
	dz = z2 - z1    
	dist = math.sqrt(dx**2 + dy**2 + dz**2)
	phi = math.degrees(math.atan2(dy, dx)) # Rotation around Y-Axis
	if dist < 0.0001:
		theta = 0
	else:
		theta = math.degrees(math.acos(dz/dist)) # Rotation around Z-Axis
	flat_item = topologic.TopologyUtility.Translate(item, -cm.X(), -cm.Y(), -cm.Z())
	flat_item = topologic.TopologyUtility.Rotate(flat_item, origin, 0, 0, 1, -phi)
	flat_item = topologic.TopologyUtility.Rotate(flat_item, origin, 0, 1, 0, -theta)
	return flat_item

class SvFaceFlatten(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Moves the input Face to the XY plane, the item's center of mass ends up at the origin
	"""
	bl_idname = 'SvFaceFlatten'
	bl_label = 'Face.Flatten'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Face'].sv_set([])
			return
		inputs = self.inputs['Face'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceFlatten)

def unregister():
	bpy.utils.unregister_class(SvFaceFlatten)
