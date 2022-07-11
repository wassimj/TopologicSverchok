import bpy
from bpy.props import FloatProperty, StringProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import numpy as np
from scipy.spatial import ConvexHull
from . import ShellByFaces, ShellExternalBoundary, TopologySelfMerge, Replication
import math

def list_level_iter(lst, level, _current_level: int= 1):
	"""
	Iterate over all lists with given nesting
	With level 1 it will return the given list
	With level 2 it will iterate over all nested lists in the main one
	If a level does not have lists on that level it will return empty list
	_current_level - for internal use only
	"""
	if _current_level < level:
		try:
			for nested_lst in lst:
				if not isinstance(nested_lst, list):
					raise TypeError
				yield from list_level_iter(nested_lst, level, _current_level + 1)
		except TypeError:
			yield []
	else:
		yield lst

def recur(input, tol):
	output = []
	if input == None:
		return []
	if isinstance(input, list):
		for anItem in input:
			output.append(recur(anItem, tol))
	else:
		output = processItem([input, tol])
	return output

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

def processItem(item):
	topology, tol = item
	returnObject = None
	try:
		returnObject = convexHull3D(topology, tol, None)
	except:
		returnObject = convexHull3D(topology, tol, 'QJ')
	return returnObject

class SvTopologyConvexHull(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Create a convex hull of the input Topology
	"""
	bl_idname = 'SvTopologyConvexHull'
	bl_label = 'Topology.ConvexHull'
	Tol: FloatProperty(name='Tol', default=0.0001, min=0, precision=4, update=updateNode)
	Level: IntProperty(name='Level', default =2,min=1, update = updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Level').prop_name='Level'
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Convex Hull')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		level = Replication.flatten(self.inputs['Level'].sv_get(deepcopy=False, default= 2))
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0][0]
		if isinstance(level,list):
			level = int(level[0])
		topologyList = list(list_level_iter(topologyList,level))
		topologyList = [Replication.flatten(t) for t in topologyList]
		outputs = []
		for t in range(len(topologyList)):
			outputs.append(recur(topologyList[t], tol))
		self.outputs['Convex Hull'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyConvexHull)

def unregister():
	bpy.utils.unregister_class(SvTopologyConvexHull)
