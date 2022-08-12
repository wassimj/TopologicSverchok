#import sys
#sys.path.append(r"D:\Anaconda3\envs\py310\Lib\site-packages")
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
#from sverchok.core.socket_data import SvGetSocketInfo

import torch
from . import Replication

def update_sockets(self, context):
	# hide all input sockets
	self.inputs['Adadelta_eps'].hide_safe = True
	self.inputs['Adadelta_lr'].hide_safe = True
	self.inputs['Adadelta_rho'].hide_safe = True
	self.inputs['Adadelta_weight_decay'].hide_safe = True
	self.inputs['Adagrad_eps'].hide_safe = True
	self.inputs['Adagrad_lr'].hide_safe = True
	self.inputs['Adagrad_lr_decay'].hide_safe = True
	self.inputs['Adagrad_weight_decay'].hide_safe = True
	self.inputs['Adam_amsgrad'].hide_safe = True
	self.inputs['Adam_betas'].hide_safe = True
	self.inputs['Adam_eps'].hide_safe = True
	self.inputs['Adam_lr'].hide_safe = True
	self.inputs['Adam_maximize'].hide_safe = True
	self.inputs['Adam_weight_decay'].hide_safe = True

	if self.Optimizers == "Adadelta":
		self.inputs['Adadelta_eps'].hide_safe = False
		self.inputs['Adadelta_lr'].hide_safe = False
		self.inputs['Adadelta_rho'].hide_safe = False
		self.inputs['Adadelta_weight_decay'].hide_safe = False
	elif self.Optimizers == "Adagrad":
		self.inputs['Adagrad_eps'].hide_safe = False
		self.inputs['Adagrad_lr'].hide_safe = False
		self.inputs['Adagrad_lr_decay'].hide_safe = False
		self.inputs['Adagrad_weight_decay'].hide_safe = False
	elif self.Optimizers == "Adam":
		self.inputs['Adam_amsgrad'].hide_safe = False
		self.inputs['Adam_betas'].hide_safe = False
		self.inputs['Adam_eps'].hide_safe = False
		self.inputs['Adam_lr'].hide_safe = False
		self.inputs['Adam_maximize'].hide_safe = False
		self.inputs['Adam_weight_decay'].hide_safe = False
	updateNode(self, context)

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

optimizers = [("Adadelta", "Adadelta", "", 1),
				("Adagrad", "Adagrad", "", 2),
				("Adam", "Adam", "", 3),
				]
"""
				("AdamW", "AdamW", "", 4),
				("SparseAdam", "SparseAdam", "", 5),
				("Adamax", "Adamax", "", 6),
				("LBFGS", "LBFGS", "", 7),
				("ASGD", "ASGD", "", 8),
				("NAdam", "NAdam", "", 9),
				("RAdam", "RAdam", "", 10),
				("RMSprop", "RMSprop", "", 11),
				("Rprop", "Rprop", "", 12),
				("SGD", "SGD", "", 13),
				]
"""

class SvDGLOptimizer(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a DGL Optimizer Object from the input parameters
	"""
	
	bl_idname = 'SvDGLOptimizer'
	bl_label = 'DGL.Optimizer'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	Optimizers: EnumProperty(name="Optimizer", description="This will be the selected optimizer from the torch.optim package. The default is Adam", default="Adam", items=optimizers, update=update_sockets)

	Adadelta_epsProp: FloatProperty(name="eps", description="term added to the denominator to improve numerical stability (default: 1e-6)", default=0.000001, precision=6, update=updateNode)
	Adadelta_lrProp: FloatProperty(name="lr", description="coefficient that scale delta before it is applied to the parameters (default: 1.0)", default=1.0, precision=6, update=updateNode)
	Adadelta_rhoProp: FloatProperty(name="rho", description="coefficient used for computing a running average of squared gradients (default: 0.9)", default=0.9, precision=6, update=updateNode)
	Adadelta_weight_decayProp: FloatProperty(name="weight_decay", description="weight decay (L2 penalty) (default: 0)", default=0, precision=6, update=updateNode)

	Adagrad_epsProp: FloatProperty(name="eps", description="term added to the denominator to improve numerical stability (default: 1e-10)", default=1e-10, precision=10, update=updateNode)
	Adagrad_lrProp: FloatProperty(name="lr", description="learning rate (default: 1e-2)", default=0.01, precision=6, update=updateNode)
	Adagrad_lr_decayProp: FloatProperty(name="lr_decay", description="learning rate decay (default: 0)", default=0, precision=6, update=updateNode)
	Adagrad_weight_decayProp: FloatProperty(name="weight_decay", description="weight decay (L2 penalty) (default: 0)", default=0, update=updateNode)

	Adam_amsgradProp: BoolProperty(name="amsgrad", description="whether to use the AMSGrad variant of this algorithm from the paper On the Convergence of Adam and Beyond (default: False)", default=False, update=updateNode)
	Adam_betasProp: FloatVectorProperty(name="betas", size=2, precision=6, description="coefficient that scale delta before it is applied to the parameters (default: (0.9, 0.999))", default=(0.9, 0.999), update=updateNode)
	Adam_epsProp: FloatProperty(name="eps", description="term added to the denominator to improve numerical stability (default: 1e-6)", default=1e-6, precision=6, update=updateNode)
	Adam_lrProp: FloatProperty(name="lr", description="learning rate (default: 1e-3)", default=0.001, precision=6, update=updateNode)
	Adam_maximizeProp: BoolProperty(name="maximize", description="maximize the params based on the objective, instead of minimizing (default: False)", default=False, update=updateNode)
	Adam_weight_decayProp: FloatProperty(name="weight_decay", description="weight decay (L2 penalty) (default: 0)", default=0, precision=6, update=updateNode)

	
	def sv_init(self, context):
		self.width = 300
		self.inputs.new('SvStringsSocket', 'Adadelta_eps').prop_name='Adadelta_epsProp'
		self.inputs.new('SvStringsSocket', 'Adadelta_lr').prop_name='Adadelta_lrProp'
		self.inputs.new('SvStringsSocket', 'Adadelta_rho').prop_name='Adadelta_rhoProp'
		self.inputs.new('SvStringsSocket', 'Adadelta_weight_decay').prop_name='Adadelta_weight_decayProp'
		self.inputs.new('SvStringsSocket', 'Adagrad_eps').prop_name='Adagrad_epsProp'
		self.inputs.new('SvStringsSocket', 'Adagrad_lr').prop_name='Adagrad_lrProp'
		self.inputs.new('SvStringsSocket', 'Adagrad_lr_decay').prop_name='Adagrad_lr_decayProp'
		self.inputs.new('SvStringsSocket', 'Adagrad_weight_decay').prop_name='Adagrad_weight_decayProp'
		self.inputs.new('SvStringsSocket', 'Adam_amsgrad').prop_name='Adam_amsgradProp'
		self.inputs.new('SvStringsSocket', 'Adam_betas').prop_name='Adam_betasProp'
		self.inputs.new('SvStringsSocket', 'Adam_eps').prop_name='Adam_epsProp'
		self.inputs.new('SvStringsSocket', 'Adam_lr').prop_name='Adam_lrProp'
		self.inputs.new('SvStringsSocket', 'Adam_maximize').prop_name='Adam_maximizeProp'
		self.inputs.new('SvStringsSocket', 'Adam_weight_decay').prop_name='Adam_weight_decayProp'
		self.outputs.new('SvStringsSocket', 'Optimizer')
		update_sockets(self, context)
		for socket in self.inputs:
			if socket.prop_name != '':
				socket.custom_draw = "SvDGLOptimizer_draw_socket"

	def SvDGLOptimizer_draw_socket(self, socket, context, layout):
		row = layout.row()
		split = row.split(factor=0.45)
		#split.row().label(text=socket.name+ '. ' + SvGetSocketInfo(socket))
		split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
		split.row().prop(self, socket.prop_name, text="")

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		layout.prop(self, "Optimizers", expand=False, text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if self.Optimizers == "Adadelta":
			epsList = self.inputs['Adadelta_eps'].sv_get(deepcopy=True)
			lrList = self.inputs['Adadelta_lr'].sv_get(deepcopy=True)
			rhoList = self.inputs['Adadelta_rho'].sv_get(deepcopy=True)
			weight_decayList = self.inputs['Adadelta_weight_decay'].sv_get(deepcopy=True)
			epsList = Replication.flatten(epsList)
			lrList = Replication.flatten(lrList)
			rhoList = Replication.flatten(rhoList)
			weight_decayList = Replication.flatten(weight_decayList)
			inputs = [[self.Optimizers], epsList, lrList, rhoList, weight_decayList]

		elif self.Optimizers == "Adagrad":
			epsList = self.inputs['Adagrad_eps'].sv_get(deepcopy=True)
			lrList = self.inputs['Adagrad_lr'].sv_get(deepcopy=True)
			lr_decayList = self.inputs['Adagrad_lr_decay'].sv_get(deepcopy=True)
			weight_decayList = self.inputs['Adagrad_weight_decay'].sv_get(deepcopy=True)
			epsList = Replication.flatten(epsList)
			lrList = Replication.flatten(lrList)
			lr_decayList = Replication.flatten(lr_decayList)
			weight_decayList = Replication.flatten(weight_decayList)
			inputs = [[self.Optimizers], epsList, lrList, lr_decayList, weight_decayList]

		elif self.Optimizers == "Adam":
			amsgradList = self.inputs['Adam_amsgrad'].sv_get(deepcopy=True)
			betasList = self.inputs['Adam_betas'].sv_get(deepcopy=True)[0]
			epsList = self.inputs['Adam_eps'].sv_get(deepcopy=True)
			lrList = self.inputs['Adam_lr'].sv_get(deepcopy=True)
			maximizeList = self.inputs['Adam_maximize'].sv_get(deepcopy=True)
			weight_decayList = self.inputs['Adam_weight_decay'].sv_get(deepcopy=True)
			amsgradList = Replication.flatten(amsgradList)
			#betasList is already taken care of.
			epsList = Replication.flatten(epsList)
			lrList = Replication.flatten(lrList)
			maximizeList = Replication.flatten(maximizeList)
			weight_decayList = Replication.flatten(weight_decayList)
			inputs = [[self.Optimizers], amsgradList, betasList, epsList, lrList, maximizeList, weight_decayList]

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
			outputs.append(anInput)
		self.outputs['Optimizer'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvDGLOptimizer)

def unregister():
	bpy.utils.unregister_class(SvDGLOptimizer)
