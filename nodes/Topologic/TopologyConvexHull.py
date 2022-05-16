import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import numpy as np
from scipy.spatial import ConvexHull
from . import ShellByFaces, ShellExternalBoundary, TopologySelfMerge
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

def convexHull3D(item, tol, option):
	if item:
		vertices = []
		_ = item.Vertices(None, vertices)
		pointList = []
		for v in vertices:
			pointList.append([v.X(), v.Y(), v.Z()])
		points = np.array(pointList)
		if option:
			hull = ConvexHull(points, qhull_options=option)
		else:
			hull = ConvexHull(points)
		hull_vertices = []
		faces = []
		for simplex in hull.simplices:
			edges = []
			for i in range(len(simplex)-1):
				sp = hull.points[simplex[i]]
				ep = hull.points[simplex[i+1]]
				sv = topologic.Vertex.ByCoordinates(sp[0], sp[1], sp[2])
				ev = topologic.Vertex.ByCoordinates(ep[0], ep[1], ep[2])
				edges.append(topologic.Edge.ByStartVertexEndVertex(sv, ev))
			sp = hull.points[simplex[-1]]
			ep = hull.points[simplex[0]]
			sv = topologic.Vertex.ByCoordinates(sp[0], sp[1], sp[2])
			ev = topologic.Vertex.ByCoordinates(ep[0], ep[1], ep[2])
			edges.append(topologic.Edge.ByStartVertexEndVertex(sv, ev))
			faces.append(topologic.Face.ByExternalBoundary(topologic.Wire.ByEdges(edges)))
	try:
		c = CellByFaces.processItem(faces, tol)
		return c
	except:
		returnTopology = TopologySelfMerge.processItem(topologic.Cluster.ByTopologies(faces))
		if returnTopology.Type() == 16:
			return ShellExternalBoundary.processItem(returnTopology)

def convexHull2D(item, tol):
	if item:
		# If topology is a vertex or edge, return the topology itself as the convex hull
		if item.Type() < 3:
			return item
		# Move the topology to the XY plane and face up
		origin = topologic.Vertex.ByCoordinates(0,0,0)
		cm = item.CenterOfMass()
		if item.Type() == 4:
			new_item = topologic.Face.ByExternalBoundary(item)
		elif item.Type() == 16:
			new_item = ShellExternalBoundary.processItem(item)
			new_item = topologic.Face.ByExternalBoundary(item)
		coords = topologic.FaceUtility.NormalAtParameters(new_item, 0.5, 0.5)
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
		print("Phi and Theta", phi, theta)
		base_item = topologic.TopologyUtility.Translate(new_item, -cm.X(), -cm.Y(), -cm.Z())
		base_item = topologic.TopologyUtility.Rotate(base_item, origin, 0, 0, 1, -phi)
		bse_item = topologic.TopologyUtility.Rotate(base_item, origin, 0, 1, 0, -theta)
		vertices = []
		_ = base_item.Vertices(None, vertices)
		pointList = []
		for v in vertices:
			pointList.append([v.X(), v.Y()])
		points = np.array(pointList)
		hull = ConvexHull(points, qhull_options='QJ')
		hull_vertices = []

		edges = []
		for simplex in hull.simplices:
			for i in range(len(simplex)-1):
				sp = hull.points[simplex[i]]
				ep = hull.points[simplex[i+1]]
				sv = topologic.Vertex.ByCoordinates(sp[0], sp[1], 0)
				ev = topologic.Vertex.ByCoordinates(ep[0], ep[1], 0)
				edges.append(topologic.Edge.ByStartVertexEndVertex(sv, ev))
			sp = hull.points[simplex[-1]]
			ep = hull.points[simplex[0]]
			sv = topologic.Vertex.ByCoordinates(sp[0], sp[1], 0)
			ev = topologic.Vertex.ByCoordinates(ep[0], ep[1], 0)
			edges.append(topologic.Edge.ByStartVertexEndVertex(sv, ev))
	clus = topologic.Cluster.ByTopologies(edges)
	clus = TopologySelfMerge.processItem(clus)
	clus = topologic.TopologyUtility.Rotate(clus, origin, 0, 1, 0, theta)
	clus = topologic.TopologyUtility.Rotate(clus, origin, 0, 0, 1, phi)
	clus = topologic.TopologyUtility.Translate(clus, cm.X(), cm.Y(), cm.Z())
	return [clus, base_item]

def processItem(item, tol):
	returnObject = None
	try:
		returnObject = convexHull3D(item, tol, None)
	except:
		returnObject = convexHull3D(item, tol, 'QJ')
	return returnObject

class SvTopologyConvexHull(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Create a convex hull of the input Topology
	"""
	bl_idname = 'SvTopologyConvexHull'
	bl_label = 'Topology.ConvexHull'
	Tol: FloatProperty(name='Tol', default=0.0001, min=0, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Convex Hull')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0][0]
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, tol))
		self.outputs['Convex Hull'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyConvexHull)

def unregister():
	bpy.utils.unregister_class(SvTopologyConvexHull)
