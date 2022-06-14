import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
#from sverchok.core.update_system import make_tree_from_nodes, do_update
from sverchok.core.update_system import UpdateTree
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.transports.memory import MemoryTransport
from specklepy.api import operations
from specklepy.api.wrapper import StreamWrapper
from specklepy.api.resources.stream import Stream
from specklepy.transports.server import ServerTransport
from specklepy.objects.geometry import *
from specklepy.logging.exceptions import SpeckleException
from bpy_speckle.convert import get_speckle_subobjects
from bpy_speckle.clients import speckle_clients
from bpy_speckle.operators.users import add_user_stream
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

def runItem(item):
	resetItem(item)
	client, stream, branch, commit = item
	transport = ServerTransport(stream.id, client)
	stream_data = operations.receive(commit.referencedObject, transport)
	host_name = client.url[8:]
	client_collection = addCollectionIfNew("Host "+host_name)
	stream_collection = addCollectionIfNew("Stream "+stream.id)
	branch_collection = addCollectionIfNew("Branch "+branch.id)
	commit_collection = addCollectionIfNew("Commit "+commit.id)
	dynamic_member_names = stream_data.get_dynamic_member_names()
	returnObjects = []
	for i, dynamic_member_name in enumerate(dynamic_member_names):
		obj_collection = stream_data[dynamic_member_name]
		if len(obj_collection) > 0:
			object_collection = addCollectionIfNew(host_name+"_"+stream.id+"_"+branch.id+"_"+commit.id+"_"+dynamic_member_name)
			for j, obj in enumerate(obj_collection):
				object_name = host_name+"_"+stream.id+"_"+branch.id+"_"+commit.id+"_"+dynamic_member_name+"_"+str(j+1)
				try:
					speckle_mesh = getattr(obj,'displayValue')[0]
					blender_mesh = mesh_to_native(speckle_mesh, object_name)
				except:
					blender_mesh = bpy.data.meshes.new(name=object_name)
					bm = bmesh.new()
					bm.verts.new((0.0, 0.0, 0.0))
					bm.to_mesh(blender_mesh)
					bm.free()

				# Delete any pre-existing object with the same name
				try:
					object_to_delete = bpy.data.objects[object_name]
					bpy.data.objects.remove(object_to_delete, do_unlink=True)
				except:
					pass
				new_object = bpy.data.objects.new(object_name, blender_mesh)
				member_names = obj.get_member_names()
				for member_name in member_names:
					attribute = getattr(obj, member_name)
					if isinstance(attribute, float) or isinstance(attribute, int) or isinstance(attribute, str):
						new_object[member_name] = attribute
				object_collection.objects.link(new_object)
				returnObjects.append(new_object)
			try:
				commit_collection.children.link(object_collection)
			except:
				pass
	try:
		branch_collection.children.link(commit_collection)
	except:
		pass
	try:
		stream_collection.children.link(branch_collection)
	except:
		pass
	try:
		client_collection.children.link(stream_collection)
	except:
		pass
	try:
		bpy.context.scene.collection.children.link(client_collection)
	except:
		pass
	return returnObjects

def resetItem(item):
	client, stream, branch, commit = item
	host_name = client.url[8:]
	collection_names = ["Commit "+commit.id, "Branch "+branch.id, "Stream "+stream.id,"Host "+host_name]
	for collection_name in collection_names:
		collection = bpy.data.collections.get(collection_name)
		if collection:
			print("Collection Objects", collection.objects)
			if collection.objects:
				for obj in collection.objects:
					bpy.data.objects.remove(obj, do_unlink=True)
			bpy.data.collections.remove(collection)
	return None

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvSpeckleReset(bpy.types.Operator, SvGenericNodeLocator):

	bl_idname = "speckle.reset"
	bl_label = "Speckle Reset"
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	def sv_execute(self, context, node):
		clientList = node.inputs['Client'].sv_get(deepcopy=True)
		streamList = node.inputs['Stream'].sv_get(deepcopy=True)
		branchList = node.inputs['Branch'].sv_get(deepcopy=True)
		commitList = node.inputs['Commit'].sv_get(deepcopy=True)
		clientList = flatten(clientList)
		streamList = flatten(streamList)
		branchList = flatten(branchList)
		commitList = flatten(commitList)

		inputs = [clientList, streamList, branchList, commitList]
		if ((node.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((node.Replication) == "Default") or ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((node.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((node.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			resetItem(anInput)
		node.outputs['Objects'].sv_set([None])
		tree = node.id_data
		UpdateTree.get(tree)
		#update_list = make_tree_from_nodes([node.name], tree)
		#update_list = update_list[1:]
		#do_update(update_list, tree.nodes)

class SvSpeckleRun(bpy.types.Operator, SvGenericNodeLocator):

	bl_idname = "speckle.run"
	bl_label = "Speckle run"
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	def sv_execute(self, context, node):
		clientList = node.inputs['Client'].sv_get(deepcopy=True)
		streamList = node.inputs['Stream'].sv_get(deepcopy=True)
		branchList = node.inputs['Branch'].sv_get(deepcopy=True)
		commitList = node.inputs['Commit'].sv_get(deepcopy=True)
		clientList = flatten(clientList)
		streamList = flatten(streamList)
		branchList = flatten(branchList)
		commitList = flatten(commitList)

		inputs = [clientList, streamList, branchList, commitList]
		if ((node.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((node.Replication) == "Default") or ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((node.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((node.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(runItem(anInput))
		node.outputs['Objects'].sv_set(outputs)
		tree = node.id_data
		update_list = make_tree_from_nodes([node.name], tree)
		update_list = update_list[1:]
		do_update(update_list, tree.nodes)

class SvSpeckleReceive(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Receive Speckle Objects   
	"""
	bl_idname = 'SvSpeckleReceive'
	bl_label = 'Speckle.Receive'
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	Output: StringProperty(name="Objects", default="", update=updateNode)

	def sv_init(self, context):
		#self.inputs[0].label = 'Auto'
		self.inputs.new('SvStringsSocket', 'Client')
		self.inputs.new('SvStringsSocket', 'Stream')
		self.inputs.new('SvStringsSocket', 'Branch')
		self.inputs.new('SvStringsSocket', 'Commit')
		self.outputs.new('SvStringsSocket', 'Objects').prop_name = 'Output'

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")
		row = layout.row(align=True)
		row.scale_y = 2
		self.wrapper_tracked_ui_draw_op(row, "speckle.reset", icon='CANCEL', text="RESET")
		row = layout.row(align=True)
		row.scale_y = 2
		self.wrapper_tracked_ui_draw_op(row, "speckle.run", icon='PLAY', text="RUN")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		self.outputs['Objects'].sv_set([None])

def register():
	bpy.utils.register_class(SvSpeckleReceive)
	bpy.utils.register_class(SvSpeckleReset)
	bpy.utils.register_class(SvSpeckleRun)

def unregister():
	bpy.utils.unregister_class(SvSpeckleReceive)
	bpy.utils.unregister_class(SvSpeckleReset)
	bpy.utils.unregister_class(SvSpeckleRun)

