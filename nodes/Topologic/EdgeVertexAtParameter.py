import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvEdgeVertexAtParameter(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Vertex at the parameter value of the input Edge
	"""
	bl_idname = 'SvEdgeVertexAtParameter'
	bl_label = 'Edge.VertexAtParameter'
	Parameter: FloatProperty(name="Parameter", default=0.5, precision=4, min=0, max=1, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.inputs.new('SvStringsSocket', 'Parameter').prop_name='Parameter'
		self.outputs.new('SvStringsSocket', 'Vertex')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		edgesList = self.inputs['Edge'].sv_get(deepcopy=False)
		parametersList = self.inputs['Parameter'].sv_get(deepcopy=False)
		if isinstance(parametersList[0], list) == False:
			parametersList = [parametersList]
		if len(edgesList) != len(parametersList):
			maxLength = max([len(edgesList), len(parametersList)])
			for i in range(len(edgesList), maxLength):
				edgesList.append(edgesList[-1])
			for i in range(len(parametersList), maxLength):
				parametersList.append(parametersList[-1])
		outputs = []
		for i in range(len(edgesList)):
			vertexList = []
			for j in range(len(parametersList[i])):
				vertexList.append(topologic.EdgeUtility.PointAtParameter(edgesList[i], parametersList[i][j]))
			outputs.append(vertexList)
		self.outputs['Vertex'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvEdgeVertexAtParameter)

def unregister():
	bpy.utils.unregister_class(SvEdgeVertexAtParameter)
