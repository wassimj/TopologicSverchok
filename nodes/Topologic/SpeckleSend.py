import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.transports.memory import MemoryTransport
from specklepy.api import operations
from specklepy.api import operations
from specklepy.api.wrapper import StreamWrapper
from specklepy.api.resources.stream import Stream
from specklepy.transports.server import ServerTransport
from specklepy.objects.geometry import *
from specklepy.logging.exceptions import SpeckleException
from bpy_speckle.convert import get_speckle_subobjects
from bpy_speckle.clients import speckle_clients
from bpy_speckle.operators.users import add_user_stream
from specklepy.objects import Base
import bmesh
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

def add_vertices(speckle_mesh, blender_mesh, scale=1.0):
    sverts = speckle_mesh.vertices
    if sverts and len(sverts) > 0:
	    for i in range(0, len(sverts), 3):
		    blender_mesh.verts.new((float(sverts[i]) * scale, float(sverts[i + 1]) * scale, float(sverts[i + 2]) * scale,))
    blender_mesh.verts.ensure_lookup_table()

def add_faces(speckle_mesh, blender_mesh, smooth=False):
	sfaces = speckle_mesh.faces
	if sfaces and len(sfaces) > 0:
		i = 0
		while i < len(sfaces):
			n = sfaces[i]
			if n < 3:
				n += 3  # 0 -> 3, 1 -> 4
			i += 1
			f = blender_mesh.faces.new([blender_mesh.verts[int(x)] for x in sfaces[i : i + n]])
			f.smooth = smooth
			i += n
		blender_mesh.faces.ensure_lookup_table()
		blender_mesh.verts.index_update()

def mesh_to_native(speckle_mesh, name, scale=1.0):
	if name in bpy.data.meshes.keys():
		blender_mesh = bpy.data.meshes[name]
	else:
		blender_mesh = bpy.data.meshes.new(name=name)
	bm = bmesh.new()
	add_vertices(speckle_mesh, bm, scale)
	add_faces(speckle_mesh, bm)
	bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
	bm.to_mesh(blender_mesh)
	bm.free()
	return blender_mesh

def addCollectionIfNew(collectionName):
	for collection in bpy.data.collections:
		if (collection.name == collectionName):
			return collection
	return bpy.data.collections.new(collectionName)

def processItem(item):
	client, stream, branch, description, message, key, data, run = item
	if not run:
		return None
	# create a base object to hold data
	base = Base()
	base[key] = data
	transport = ServerTransport(stream.id, client)
	# and send the data to the server and get back the hash of the object
	obj_id = operations.send(base, [transport])

	# now create a commit on that branch with your updated data!
	commit_id = client.commit.create(
		stream.id,
		obj_id,
		"gbxml",
		message=message,
	)
	print("COMMIT ID", commit_id)
	for commit in branch.commits.items:
		print("  VS. COMMIT.ID", commit.id)
		if commit.id == commit_id:
			return commit
	return None

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvSpeckleSend(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Send Speckle Data   
	"""
	bl_idname = 'SvSpeckleSend'
	bl_label = 'Speckle.Send'
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	BranchName: StringProperty(name='Branch Name', default="Untitled",update=updateNode)
	Description: StringProperty(name='Description', default="",update=updateNode)
	Message: StringProperty(name='Message', default="",update=updateNode)
	Key: StringProperty(name='Key', default="DefaultKey",update=updateNode)
	Run: BoolProperty(name="Run", default=False, update=updateNode)


	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Client')
		self.inputs.new('SvStringsSocket', 'Stream')
		self.inputs.new('SvStringsSocket', 'Branch')
		self.inputs.new('SvStringsSocket', 'Description').prop_name='Description'
		self.inputs.new('SvStringsSocket', 'Message').prop_name='Message'
		self.inputs.new('SvStringsSocket', 'Key').prop_name='Key'
		self.inputs.new('SvStringsSocket', 'Data')
		self.inputs.new('SvStringsSocket', 'Run').prop_name = 'Run'
		self.outputs.new('SvStringsSocket', 'Commit')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		clientList = self.inputs['Client'].sv_get(deepcopy=True)
		streamList = self.inputs['Stream'].sv_get(deepcopy=True)
		branchList = self.inputs['Branch'].sv_get(deepcopy=True)
		descriptionList = self.inputs['Description'].sv_get(deepcopy=True)
		messageList = self.inputs['Message'].sv_get(deepcopy=True)
		keyList = self.inputs['Key'].sv_get(deepcopy=True)
		dataList = self.inputs['Data'].sv_get(deepcopy=True)
		runList = self.inputs['Run'].sv_get(deepcopy=True)
		clientList = flatten(clientList)
		streamList = flatten(streamList)
		branchList = flatten(branchList)
		descriptionList = flatten(descriptionList)
		messageList = flatten(messageList)
		keyList = flatten(keyList)
		dataList = flatten(dataList)
		runList = flatten(runList)
		inputs = [clientList, streamList, branchList, descriptionList, messageList, keyList, dataList, runList]
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
		self.outputs['Commit'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvSpeckleSend)

def unregister():
    bpy.utils.unregister_class(SvSpeckleSend)
