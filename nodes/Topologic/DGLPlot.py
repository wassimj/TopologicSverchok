import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

import torch
from . import Replication
import os
import pandas as pd
import plotly.express as px

chart_type = [("Line", "Line", "", 1),
				  ("Bar", "Bar", "", 2),
				  ("Scatter", "Scatter", "", 3)]

def processItem(item):
	data, data_labels, chart_title, x_title, x_spacing, y_title, y_spacing, use_markers, chart_type = item
	dlist = list(map(list, zip(*data)))
	df = pd.DataFrame(dlist, columns=data_labels)
	if chart_type == "Line":
		fig = px.line(df, x = data_labels[0], y=data_labels[1:], title=chart_title, markers=use_markers)
	elif chart_type == "Bar":
		fig = px.bar(df, x = data_labels[0], y=data_labels[1:], title=chart_title)
	elif chart_type == "Scatter":
		fig = px.scatter(df, x = data_labels[0], y=data_labels[1:], title=chart_title)
	else:
		raise NotImplementedError
	fig.layout.xaxis.title=x_title
	fig.layout.xaxis.dtick=x_spacing
	fig.layout.yaxis.title=y_title
	fig.layout.yaxis.dtick= y_spacing
	#fig.show()
	import os
	from os.path import expanduser
	home = expanduser("~")
	filePath = os.path.join(home, "dgl_result.html")
	html = fig.to_html(full_html=True, include_plotlyjs=True)
	# save html file
	with open(filePath, "w") as f:
		f.write(html)
	os.system("start "+filePath)

def sv_execute(node):
	dataList = node.inputs['Data'].sv_get(deepcopy=True)
	dataLabelsList = node.inputs['Data Labels'].sv_get(deepcopy=True)
	chartTitleList = node.inputs['Chart Title'].sv_get(deepcopy=True)
	xAxisTitleList = node.inputs['X-Axis Title'].sv_get(deepcopy=True)
	xSpacingList = node.inputs['X Spacing'].sv_get(deepcopy=True)
	yAxisTitleList = node.inputs['Y-Axis Title'].sv_get(deepcopy=True)
	ySpacingList = node.inputs['Y Spacing'].sv_get(deepcopy=True)
	useMarkersList = node.inputs['Use Markers'].sv_get(deepcopy=True)
	chartTypeList = node.inputs['Chart Type'].sv_get(deepcopy=True)

	chartTitleList = Replication.flatten(chartTitleList)
	xAxisTitleList = Replication.flatten(xAxisTitleList)
	xSpacingList = Replication.flatten(xSpacingList)
	yAxisTitleList = Replication.flatten(yAxisTitleList)
	ySpacingList = Replication.flatten(ySpacingList)
	useMarkersList = Replication.flatten(useMarkersList)
	chartTypeList = Replication.flatten(chartTypeList)

	inputs = [dataList, dataLabelsList, chartTitleList, xAxisTitleList, xSpacingList, yAxisTitleList, ySpacingList, useMarkersList, chartTypeList]
	if ((node.Replication) == "Default"):
		inputs = Replication.iterate(inputs)
		inputs = Replication.transposeList(inputs)
	if ((node.Replication) == "Trim"):
		inputs = Replication.trim(inputs)
		inputs = Replication.transposeList(inputs)
	elif ((node.Replication) == "Iterate"):
		inputs = Replication.iterate(inputs)
		inputs = Replication.transposeList(inputs)
	elif ((node.Replication) == "Repeat"):
		inputs = Replication.repeat(inputs)
		inputs = Replication.transposeList(inputs)
	elif ((node.Replication) == "Interlace"):
		inputs = list(Replication.interlace(inputs))
	for anInput in inputs:
		processItem(anInput)

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDGLPlotRun(bpy.types.Operator, SvGenericNodeLocator):

	bl_idname = "dgl.plotrun"
	bl_label = "DGL.PlotRun"
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_execute(self, context, node):
		sv_execute(node)

class SvDGLPlot(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates an interactive plot from the input parameters
	"""
	
	bl_idname = 'SvDGLPlot'
	bl_label = 'DGL.Plot'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	ChartTitleProp: StringProperty(name="Chart Title", description="The title of the chart", default="Untitled", update=updateNode)
	XAxisTitleProp: StringProperty(name="X-Axis Title", description="The title of the x-axis", default="X-Axis Title", update=updateNode)
	XSpacingProp: FloatProperty(name="X Spacing", description="The distance between x-axis grid lines (Default 1)", default=1, min=0.000001, update=updateNode)
	YAxisTitleProp: StringProperty(name="Y-Axis Title", description="The title of the y-axis", default="Y-Axis Title", update=updateNode)
	YSpacingProp: FloatProperty(name="Y Spacing", description="The distance between y-axis grid lines (Default 1)", default=1, min=0.000001, update=updateNode)
	UseMarkersProp: BoolProperty(name="Use Markers", description="Add markers to data points", default=False, update=updateNode)
	ChartTypeProp: EnumProperty(name="Chart Type", description="Select the type of chart to display. (Default: Line)", default="Line", items=chart_type, update=updateNode)
	AutoRunProp: BoolProperty(name="Auto Run", description="Automatically plot the results", default=False, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Data')
		self.inputs.new('SvStringsSocket', 'Data Labels')
		self.inputs.new('SvStringsSocket', 'Chart Title').prop_name = 'ChartTitleProp'
		self.inputs.new('SvStringsSocket', 'X-Axis Title').prop_name = 'XAxisTitleProp'
		self.inputs.new('SvStringsSocket', 'X Spacing').prop_name = 'XSpacingProp'
		self.inputs.new('SvStringsSocket', 'Y-Axis Title').prop_name = 'YAxisTitleProp'
		self.inputs.new('SvStringsSocket', 'Y Spacing').prop_name = 'YSpacingProp'
		self.inputs.new('SvStringsSocket', 'Use Markers').prop_name='UseMarkersProp'
		self.inputs.new('SvStringsSocket', 'Chart Type').prop_name='ChartTypeProp'
		self.inputs.new('SvStringsSocket', 'Auto-Run').prop_name="AutoRunProp"

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		row = layout.row(align=True)
		#row.scale_y = 2
		#self.wrapper_tracked_ui_draw_op(row, "dgl.plotrun", icon='PLAY', text="RUN")

	def process(self):
		autorunList = self.inputs['Auto-Run'].sv_get(deepcopy=True)
		autorunList = Replication.flatten(autorunList)
		if autorunList[0]:
			sv_execute(self)



def register():
	bpy.utils.register_class(SvDGLPlot)
	bpy.utils.register_class(SvDGLPlotRun)

def unregister():
	bpy.utils.unregister_class(SvDGLPlot)
	bpy.utils.unregister_class(SvDGLPlotRun)
