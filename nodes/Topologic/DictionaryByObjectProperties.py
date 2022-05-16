import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import idprop

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Dictionary
import time
from . import Replication
from . import DictionaryByKeysValues

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

def processItem(item):
	bObject, keys, importAll = item
	dictKeys = []
	dictValues = []

	if importAll:
		dictKeys.append("Name")
		dictValues.append(bObject.name)
		dictKeys.append("Color")
		dictValues.append([bObject.color[0], bObject.color[1], bObject.color[2], bObject.color[3]])
		dictKeys.append("Location")
		dictValues.append([bObject.location[0], bObject.location[1], bObject.location[2]])
		dictKeys.append("Scale")
		dictValues.append([bObject.scale[0], bObject.scale[1], bObject.scale[2]])
		dictKeys.append("Rotation")
		dictValues.append([bObject.rotation_euler[0], bObject.rotation_euler[1], bObject.rotation_euler[2]])
		dictKeys.append("Dimensions")
		dictValues.append([bObject.dimensions[0], bObject.dimensions[1], bObject.dimensions[2]])
		for k, v in bObject.items():
			if isinstance(v, bool) or isinstance(v, int) or isinstance(v, float) or isinstance(v, str):
				dictKeys.append(str(k))
				dictValues.append(v)
	else:
		for k in keys:
			try:
				v = bObject[k]
				if v:
					if isinstance(v, bool) or isinstance(v, int) or isinstance(v, float) or isinstance(v, str):
						dictKeys.append(str(k))
						dictValues.append(v)
			except:
				if k.lower() == "name":
					dictKeys.append("Name")
					dictValues.append(bObject.name)
				elif k.lower() == "color":
					dictKeys.append("Color")
					dictValues.append([bObject.color[0], bObject.color[1], bObject.color[2], bObject.color[3]])
				elif k.lower() == "location":
					dictKeys.append("Location")
					dictValues.append([bObject.location[0], bObject.location[1], bObject.location[2]])
				elif k.lower() == "scale":
					dictKeys.append("Scale")
					dictValues.append([bObject.scale[0], bObject.scale[1], bObject.scale[2]])
				elif k.lower() == "rotation":
					dictKeys.append("Rotation")
					dictValues.append([bObject.rotation_euler[0], bObject.rotation_euler[1], bObject.rotation_euler[2]])
				elif k.lower() == "dimensions":
					dictKeys.append("Dimensions")
					dictValues.append([bObject.dimensions[0], bObject.dimensions[1], bObject.dimensions[2]])
				else:
					raise Exception("Dictionary.ByObjectProperties: Key \""+k+"\" does not exist in the properties of object \""+bObject.name+"\".")

	return DictionaryByKeysValues.processItem([dictKeys, dictValues])

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDictionaryByObjectProperties(bpy.types.Node, SverchCustomTreeNode):

	"""
	Triggers: Topologic
	Tooltip: Creates a dictionary from the custom properties of the input Blender Object
	"""
	bl_idname = 'SvDictionaryByObjectProperties'
	bl_label = 'Dictionary.ByObjectProperties'
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	ImportAllProp: BoolProperty(name="Import All", description="Import all Object Properties", default=False, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Object')
		self.inputs.new('SvStringsSocket', 'Key')
		self.inputs.new('SvStringsSocket', 'Import All').prop_name='ImportAllProp'
		self.outputs.new('SvStringsSocket', 'Dictionary')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		objectList = self.inputs['Object'].sv_get(deepcopy=True)
		objectList = Replication.flatten(objectList)
		if (self.inputs['Key'].is_linked):
			keyList = self.inputs['Key'].sv_get(deepcopy=True)
		else:
			keyList = [['']]
		importAllList = self.inputs['Import All'].sv_get(deepcopy=True)
		importAllList = Replication.flatten(importAllList)
		inputs = [objectList, keyList, importAllList]
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
		self.outputs['Dictionary'].sv_set(outputs)
		end = time.time()
		print("Dictionary.ByObjectProperties Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvDictionaryByObjectProperties)

def unregister():
    bpy.utils.unregister_class(SvDictionaryByObjectProperties)
