import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication
import math

def isOnPlane(v, plane, tolerance):
	x, y, z = v
	a, b, c, d = plane
	if math.fabs(a*x + b*y + c*z + d) <= tolerance:
		return True
	return False

def plane(v1, v2, v3):
	a1 = v2.X() - v1.X() 
	b1 = v2.Y() - v1.Y() 
	c1 = v2.Z() - v1.Z() 
	a2 = v3.X() - v1.X() 
	b2 = v3.Y() - v1.Y() 
	c2 = v3.Z() - v1.Z() 
	a = b1 * c2 - b2 * c1 
	b = a2 * c1 - a1 * c2 
	c = a1 * b2 - b1 * a2 
	d = (- a * v1.X() - b * v1.Y() - c * v1.Z())
	return [a,b,c,d]

def processItem(item):
	topology, tolerance = item
	vertices = []
	_ = topology.Vertices(None, vertices)

	result = True
	if len(vertices) <= 3:
		result = True
	else:
		p = plane(vertices[0], vertices[1], vertices[2])
		for i in range(len(vertices)):
			if isOnPlane([vertices[i].X(), vertices[i].Y(), vertices[i].Z()], p, tolerance) == False:
				result = False
				break
	return result

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvTopologyIsPlanar(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the vertices of the input Topology are coplanar. Outputs False otherwise   
	"""
	bl_idname = 'SvTopologyIsPlanar'
	bl_label = 'Topology.IsPlanar'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Is Planar')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = self.inputs[0].sv_get(deepcopy=False)
		toleranceList = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)
		topologyList = Replication.flatten(topologyList)
		toleranceList = Replication.flatten(toleranceList)
		inputs = [topologyList, toleranceList]
		if ((self.Replication) == "Default"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		if ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = Replication.repeat(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(Replication.interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Is Planar'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyIsPlanar)

def unregister():
	bpy.utils.unregister_class(SvTopologyIsPlanar)
