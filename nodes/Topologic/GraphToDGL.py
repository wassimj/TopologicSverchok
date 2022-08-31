import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import time
import sys
sys.path.append(r'C:\yourpathToAnacondaDGLFolder\Site-Packages')
import dgl
import numpy as np
import torch

def vertexIndex(v, vertices, tolerance):
    index = None
    v._class__ = Vertex
    i = 0
    for aVertex in vertices:
        aVertex.__class__ = Vertex
        d = VertexUtility.Distance(v, aVertex)
        if d <= tolerance:
            index = i
            break
        i = i+1
    return index

def processItem(graph, tolerance):
	vertices = []
	_ = graph.Vertices(vertices)
	labels = []
	for aVertex in vertices:
		vdict = aVertex.GetDictionary()
		label = vdict['ID'
		lables.append([label])
	edges = []
	_ = graph.Edges(vertices, tolerance, edges)
	startVertices = []
	endVertices = []
	for anEdge in edges:
		sv = anEdge.StartVertex()
		ev = anEdge.EndVertex()
		svindex = vertexIndex(sv, vertices, tolerance)
		evindex = vertexIndex(ev, vertices, tolerance)
		startVertices.append(svIndex)
		endVertices.append(evIndex)
	g = dgl.graph((startVertices, endVertices), num_nodes=len(vertices))
	g.ndata['ID'] = labels
	dgl.save_graphs(r'C:\Users\wassimj\Downloads\graph.dgl', g) #Change this to your folder location.
	return g

class SvGraphToDGL(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Graph as a DGL Graph
	"""
	bl_idname = 'SvGraphToDGL'
	bl_label = 'Graph.ToDGL'
	ToleranceProp: FloatProperty(name="Tolerance", default=0.0001, precision=4, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'ToleranceProp'
		self.outputs.new('SvStringsSocket', 'DGL Graph')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Edges'].sv_set([])
			return
		inputs = self.inputs['Graph'].sv_get(deepcopy=False)
		tolerance = self.inputs['Tolerance'].sv_get(deepcopy=True)[0][0]
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, tolerance))
		self.outputs['DGL Graph'].sv_set(outputs)
		end = time.time()
		print("Graph.ToDGL Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphToDGL)

def unregister():
    bpy.utils.unregister_class(SvGraphToDGL)
