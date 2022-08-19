import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import numpy as np
from numpy import arctan, pi, signbit
from numpy.linalg import norm
import math

import topologic
from . import Replication, FaceNormalAtParameters, TopologySelfMerge

from math import sqrt

def angle_between(v1, v2):
	u1 = v1 / norm(v1)
	u2 = v2 / norm(v2)
	y = u1 - u2
	x = u1 + u2
	if norm(x) == 0:
		return 0
	a0 = 2 * arctan(norm(y) / norm(x))
	if (not signbit(a0)) or signbit(pi - a0):
		return a0
	elif signbit(a0):
		return 0
	else:
		return pi

def collinear(v1, v2, tol):
	ang = angle_between(v1, v2)
	if math.isnan(ang) or math.isinf(ang):
		raise Exception("Face.IsCollinear - Error: Could not determine the angle between the input faces")
	elif abs(ang) < tol or abs(pi - ang) < tol:
		return True
	return False

# Adapted from https://github.com/erikm0111/Clustering/blob/master/sim_matrix_clustering/clustering.py

def process_input(line, samples):
    x, y = line.split(",")
    samples.append((float(x.strip()), float(y.strip())))
    return samples

def sumRow(matrix, i):
    return np.sum(matrix[i,:])

def buildSimilarityMatrix(samples, tol):
    numOfSamples = len(samples)
    matrix = np.zeros(shape=(numOfSamples, numOfSamples))
    for i in range(len(matrix)):
        for j in range(len(matrix)):
            if collinear(samples[i], samples[j], tol):
                matrix[i,j] = 1
    return matrix

def determineRow(matrix):
    maxNumOfOnes = -1
    row = -1
    for i in range(len(matrix)):
        if maxNumOfOnes < sumRow(matrix, i):
            maxNumOfOnes = sumRow(matrix, i)
            row = i
    return row

def categorizeIntoClusters(matrix):
    groups = []
    while np.sum(matrix) > 0:
        group = []
        row = determineRow(matrix)
        indexes = addIntoGroup(matrix, row)
        groups.append(indexes)
        matrix = deleteChosenRowsAndCols(matrix, indexes)
    return groups

def addIntoGroup(matrix, ind):
    change = True
    indexes = []
    for col in range(len(matrix)):
        if matrix[ind, col] == 1:
            indexes.append(col)
    while change == True:
        change = False
        numIndexes = len(indexes)
        for i in indexes:
            for col in range(len(matrix)):
                if matrix[i, col] == 1:
                    if col not in indexes:
                        indexes.append(col)
        numIndexes2 = len(indexes)
        if numIndexes != numIndexes2:
            change = True
    return indexes

def deleteChosenRowsAndCols(matrix, indexes):
    for i in indexes:
        matrix[i,:] = 0
        matrix[:,i] = 0
    return matrix

replication = [("Default", "Default", "", 1), ("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

def processItem(item):
	topology, tol = item
	faces = []
	_ = topology.Faces(None, faces)
	normals = []
	for aFace in faces:
		normals.append(FaceNormalAtParameters.processItem([aFace, 0.5, 0.5], "XYZ", 3))
	# build a matrix of similarity
	mat = buildSimilarityMatrix(normals, tol)
	categories = categorizeIntoClusters(mat)
	returnList = []
	for aCategory in categories:
		tempList = []
		if len(aCategory) > 0:
			for index in aCategory:
				tempList.append(faces[index])
			returnList.append(TopologySelfMerge.processItem(topologic.Cluster.ByTopologies(tempList)))
	return returnList

class SvTopologyClusterFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Clusters the Faces of the input Topology according to the input parameters
	"""
	bl_idname = 'SvTopologyClusterFaces'
	bl_label = 'Topology.ClusterFaces'
	Tol: FloatProperty(name='Tol', default=0.0001, min=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Clusters')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Clusters'].sv_set([])
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=True)
		topologyList = Replication.flatten(topologyList)
		toleranceList = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)
		toleranceList = Replication.flatten(toleranceList)
		inputs = [topologyList, toleranceList]
		if ((self.Replication) == "Default"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Trim"):
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
		self.outputs['Clusters'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologyClusterFaces)

def unregister():
	bpy.utils.unregister_class(SvTopologyClusterFaces)
