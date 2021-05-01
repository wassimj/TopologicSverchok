import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def matchLengths(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

def processItem(item):
	face = item[0]
	wire = item[1]
	reverseWire = item[2]
	return topologic.FaceUtility.TrimByWire(face, wire, reverseWire)
		
class SvFaceTrimByWire(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Trims the input Face by the input planar closed Wire   
	"""
	bl_idname = 'SvFaceTrimByWire'
	bl_label = 'Face.TrimByWire'
	ReverseWire: BoolProperty(name="Reverse Wire", default=False, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.inputs.new('SvStringsSocket', 'Wire')
		self.inputs.new('SvStringsSocket', 'Reverse Wire').prop_name = 'ReverseWire'
		self.outputs.new('SvStringsSocket', 'Face')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		faceList = flatten(faceList)
		wireList = self.inputs['Wire'].sv_get(deepcopy=False)
		wireList = flatten(wireList)
		reverseWireList = self.inputs['Reverse Wire'].sv_get(deepcopy=False)[0]
		reverseWireList = [reverseWireList]
		matchLengths([faceList, wireList, reverseWireList])
		inputs = zip(faceList, wireList, reverseWireList)
		outputs = []
		for anInput in inputs:
			outputs = processItem(anInput)
		self.outputs['Face'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceTrimByWire)

def unregister():
	bpy.utils.unregister_class(SvFaceTrimByWire)
