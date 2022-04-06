import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

from specklepy.api.client import SpeckleClient
from specklepy.api.wrapper import StreamWrapper
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

def streamByID(item):
	stream_list, stream_id = item
	for stream in stream_list:
		if stream.id == stream_id:
			return stream
	return None

def streamsByClient(client):
	return client.stream.list()

def branchesByStream(item):
	client, stream = item
	bList = client.branch.list(stream.id)
	branches = []
	for b in bList:
		branches.append(client.branch.get(stream.id, b.name))
	return branches

def commitsByBranch(item):
	return item.commits.items

def commitByID(item):
	commit_list, commit_id = item
	for commit in commit_list:
		if commit.id == commit_id:
			return commit
	return None

def processItem(item):
	url, token = item
	# provide any stream, branch, commit, object, or globals url
	wrapper = StreamWrapper(url)
	client = wrapper.get_client()
	client.authenticate_with_token(token)
	streams = streamsByClient(client)
	stream = streamByID([streams, wrapper.stream_id])
	return stream

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvSpeckleStreamByURL(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Retrieves the Speckle Stream from the input URL   
	"""
	bl_idname = 'SvSpeckleStreamByURL'
	bl_label = 'Speckle.StreamByURL'
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	Token: StringProperty(name='Token', default="",update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'URL')
		self.inputs.new('SvStringsSocket', 'Token').prop_name='Token'
		self.outputs.new('SvStringsSocket', 'Stream')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		urlList = self.inputs['URL'].sv_get(deepcopy=True)
		urlList = flatten(urlList)
		tokenList = self.inputs['Token'].sv_get(deepcopy=True)
		tokenList = flatten(tokenList)
		inputs = [urlList, tokenList]
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
		self.outputs['Stream'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvSpeckleStreamByURL)

def unregister():
    bpy.utils.unregister_class(SvSpeckleStreamByURL)
