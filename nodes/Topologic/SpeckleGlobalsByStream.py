import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from specklepy.transports.server import ServerTransport

from specklepy.api.client import SpeckleClient
from specklepy.api import operations
from specklepy.objects import Base
import time

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def repeat(list):
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

# From https://stackoverflow.com/questions/34432056/repeat-elements-of-list-between-each-other-until-we-reach-a-certain-length
def onestep(cur,y,base):
    # one step of the iteration
    if cur is not None:
        y.append(cur)
        base.append(cur)
    else:
        y.append(base[0])  # append is simplest, for now
        base = base[1:]+[base[0]]  # rotate
    return base

def iterate(list):
	maxLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		for i in range(len(anItem), maxLength):
			anItem.append(None)
		y=[]
		base=[]
		for cur in anItem:
			base = onestep(cur,y,base)
			# print(base,y)
		returnList.append(y)
	return returnList

def trim(list):
	minLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength < minLength:
			minLength = newLength
	for anItem in list:
		anItem = anItem[:minLength]
		returnList.append(anItem)
	return returnList

# Adapted from https://stackoverflow.com/questions/533905/get-the-cartesian-product-of-a-series-of-lists
def interlace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in interlace(ar_list[1:]):
                yield [a,]+prod

def transposeList(l):
	length = len(l[0])
	returnList = []
	for i in range(length):
		tempRow = []
		for j in range(len(l)):
			tempRow.append(l[j][i])
		returnList.append(tempRow)
	return returnList

def processBase(base):
	dictionary = {}
	dynamic_member_names = base.get_dynamic_member_names()
	for dynamic_member_name in dynamic_member_names:
		attribute = base[dynamic_member_name]
		if isinstance(attribute, float) or isinstance(attribute, int) or isinstance(attribute, str) or isinstance(attribute, list):
			dictionary[dynamic_member_name] = attribute
		if isinstance(attribute, Base):
			dictionary[dynamic_member_name] = processBase(attribute)
	return dictionary

def processItem(item):
	client, stream = item
	transport = ServerTransport(client=client, stream_id=stream.id)

	# get the `globals` branch
	branch = client.branch.get(stream.id, "globals")

	# get the latest commit
	if len(branch.commits.items) > 0:
		latest_commit = branch.commits.items[0]

		# receive the globals object
		globs = operations.receive(latest_commit.referencedObject, transport)
		return processBase(globs)
	return None

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvSpeckleGlobalsByStream(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Retrieves the Speckle Globals from the input Stream   
	"""
	bl_idname = 'SvSpeckleGlobalsByStream'
	bl_label = 'Speckle.GlobalsByStream'
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Client')
		self.inputs.new('SvStringsSocket', 'Stream')
		self.outputs.new('SvStringsSocket', 'Globals')


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		clientList = self.inputs['Client'].sv_get(deepcopy=True)
		streamList = self.inputs['Stream'].sv_get(deepcopy=True)
		clientList = flatten(clientList)
		streamList = flatten(streamList)
		inputs = [clientList, streamList]
		if ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Default") or ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Globals'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvSpeckleGlobalsByStream)

def unregister():
    bpy.utils.unregister_class(SvSpeckleGlobalsByStream)
