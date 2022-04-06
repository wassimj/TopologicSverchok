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
import webbrowser

from specklepy.objects.geometry import Mesh, Curve, Interval, Box, Point, Polyline
from specklepy.objects.other import *
from bpy_speckle.functions import _report
from bpy_speckle.convert.util import (
    get_blender_custom_properties,
    make_knots,
    to_argb_int,
)

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

# From Speckle's OOTB Blender connector
UNITS = "m"

CAN_CONVERT_TO_SPECKLE = ("MESH", "CURVE", "EMPTY")


def convert_to_speckle(blender_object, scale, desgraph=None):
    blender_type = blender_object.type
    if blender_type not in CAN_CONVERT_TO_SPECKLE:
        return

    speckle_objects = []
    speckle_material = material_to_speckle(blender_object)
    if desgraph:
        blender_object = blender_object.evaluated_get(desgraph)
    converted = None
    if blender_type == "MESH":
        converted = mesh_to_speckle(blender_object, blender_object.data, scale)
    elif blender_type == "CURVE":
        converted = icurve_to_speckle(blender_object, blender_object.data, scale)
    elif blender_type == "EMPTY":
        converted = empty_to_speckle(blender_object, scale)
    if not converted:
        return None

    if isinstance(converted, list):
        speckle_objects.extend([c for c in converted if c != None])
    else:
        speckle_objects.append(converted)
    for so in speckle_objects:
        so.properties = get_blender_custom_properties(blender_object)
        so.applicationId = so.properties.pop("applicationId", None)

        if speckle_material:
            so["renderMaterial"] = speckle_material

        # Set object transform
        if blender_type != "EMPTY":
            so.properties["transform"] = transform_to_speckle(
                blender_object.matrix_world
            )

    return speckle_objects


def mesh_to_speckle(blender_object, data, scale=1.0):
    if data.loop_triangles is None or len(data.loop_triangles) < 1:
        data.calc_loop_triangles()

    mat = blender_object.matrix_world

    verts = [tuple(mat @ x.co * scale) for x in data.vertices]

    faces = [p.vertices for p in data.polygons]
    unit_system = bpy.context.scene.unit_settings.system

    sm = Mesh(
        name=blender_object.name,
        vertices=list(sum(verts, ())),
        faces=[],
        colors=[],
        textureCoordinates=[],
        units="m" if unit_system == "METRIC" else "ft",
        bbox=Box(area=0.0, volume=0.0),
    )

    if data.uv_layers.active:
        for vt in data.uv_layers.active.data:
            sm.textureCoordinates.extend([vt.uv.x, vt.uv.y])

    for f in faces:
        n = len(f)
        if n == 3:
            sm.faces.append(0)
        elif n == 4:
            sm.faces.append(1)
        else:
            sm.faces.append(n)
        sm.faces.extend(f)

    return [sm]

def poly_to_speckle(matrix, spline, scale, name=None):
    points = [tuple(matrix @ pt.co.xyz * scale) for pt in spline.points]

    length = spline.calc_length()
    domain = Interval(start=0, end=length, totalChildrenCount=0)
    return Polyline(
        name=name,
        closed=bool(spline.use_cyclic_u),
        value=list(sum(points, ())),  # magic (flatten list of tuples)
        length=length,
        domain=domain,
        bbox=Box(area=0.0, volume=0.0),
        area=0,
        units=UNITS,
    )


def icurve_to_speckle(blender_object, data, scale=1.0):
    UNITS = "m" if bpy.context.scene.unit_settings.system == "METRIC" else "ft"

    if blender_object.type != "CURVE":
        return None

    blender_object = blender_object.evaluated_get(bpy.context.view_layer.depsgraph)

    mat = blender_object.matrix_world

    curves = []

    if data.bevel_mode == "OBJECT" and data.bevel_object != None:
        mesh = mesh_to_speckle(blender_object, blender_object.to_mesh(), scale)
        curves.extend(mesh)

    for spline in data.splines:
        if spline.type == "BEZIER":
            curves.append(bezier_to_speckle(mat, spline, scale, blender_object.name))

        elif spline.type == "NURBS":
            curves.append(nurbs_to_speckle(mat, spline, scale, blender_object.name))

        elif spline.type == "POLY":
            curves.append(poly_to_speckle(mat, spline, scale, blender_object.name))

    return curves


def ngons_to_speckle_polylines(blender_object, data, scale=1.0):
    UNITS = "m" if bpy.context.scene.unit_settings.system == "METRIC" else "ft"

    if blender_object.type != "MESH":
        return None

    mat = blender_object.matrix_world

    verts = data.vertices
    polylines = []
    for i, poly in enumerate(data.polygons):
        value = []
        for v in poly.vertices:
            value.extend(mat @ verts[v].co * scale)

        domain = Interval(start=0, end=1)
        poly = Polyline(
            name="{}_{}".format(blender_object.name, i),
            closed=True,
            value=value,  # magic (flatten list of tuples)
            length=0,
            domain=domain,
            bbox=Box(area=0.0, volume=0.0),
            area=0,
            units=UNITS,
        )

        polylines.append(poly)

    return polylines

def transform_to_speckle(blender_transform, scale=1.0):
    units = "m" if bpy.context.scene.unit_settings.system == "METRIC" else "ft"
    value = [y for x in blender_transform for y in x]
    # scale the translation
    for i in (3, 7, 11):
        value[i] *= scale

    return Transform(value=value, units=units)

def material_to_speckle(blender_object) -> RenderMaterial:
    """Create and return a render material from a blender object"""
    if not getattr(blender_object.data, "materials", None):
        return

    blender_mat = blender_object.data.materials[0]
    if not blender_mat:
        return

    speckle_mat = RenderMaterial()
    speckle_mat.name = blender_mat.name

    if blender_mat.use_nodes is True and blender_mat.node_tree.nodes.get(
        "Principled BSDF"
    ):
        inputs = blender_mat.node_tree.nodes["Principled BSDF"].inputs
        speckle_mat.diffuse = to_argb_int(inputs["Base Color"].default_value)
        speckle_mat.emissive = to_argb_int(inputs["Emission"].default_value)
        speckle_mat.roughness = inputs["Roughness"].default_value
        speckle_mat.metalness = inputs["Metallic"].default_value
        speckle_mat.opacity = inputs["Alpha"].default_value

    else:
        speckle_mat.diffuse = to_argb_int(blender_mat.diffuse_color)
        speckle_mat.metalness = blender_mat.metallic
        speckle_mat.roughness = blender_mat.roughness

    return speckle_mat

def block_def_to_speckle(blender_definition, scale=1.0):
    geometry = []
    for geo in blender_definition.objects:
        geometry.extend(convert_to_speckle(geo, scale))
    block_def = BlockDefinition(
        units=UNITS,
        name=blender_definition.name,
        geometry=geometry,
        basePoint=Point(units=UNITS),
    )
    blender_props = get_blender_custom_properties(blender_definition)
    block_def.applicationId = blender_props.pop("applicationId", None)
    return block_def


def block_instance_to_speckle(blender_instance, scale=1.0):
	return BlockInstance(
        blockDefinition=block_def_to_speckle(
            blender_instance.instance_collection, scale
        ),
        transform=transform_to_speckle(blender_instance.matrix_world),
        name=blender_instance.name,
        units=UNITS,
    )


def empty_to_speckle(blender_object, scale=1.0):
	# probably an instance collection (block) so let's try it
	try:
		geo = blender_object.instance_collection.objects.items()
		return block_instance_to_speckle(blender_object, scale)
	except AttributeError as err:
		_report(
			f"No instance collection found in empty. Skipping object {blender_object.name}"
		)
		return None
# END

def processItem(item):
	client, stream, branch, description, message, key, blender_object, openURL, run = item
	if not run:
		return None
	# create a base object to hold data
	#base = Base()
	#base[key] = obj
	transport = ServerTransport(stream.id, client)
	# and send the data to the server and get back the hash of the object
	print("Blender Object:", blender_object)
	base = convert_to_speckle(blender_object, 1.0, desgraph=None)
	obj_id = operations.send(base[0], [transport])

	# now create a commit on that branch with your updated data!
	commit_id = client.commit.create(
		stream.id,
		obj_id,
		branch.name,
		message=message,
	)
	web_address = client.url+"/streams/"+stream.id+"/commits/"+commit_id
	if openURL:
		webbrowser.open(web_address)
	return web_address

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvSpeckleSendObject(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Send Blender Object to Speckle
	"""
	bl_idname = 'SvSpeckleSendObject'
	bl_label = 'Speckle.SendObject'
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)
	BranchName: StringProperty(name='Branch Name', default="main",update=updateNode)
	Description: StringProperty(name='Description', default="",update=updateNode)
	Message: StringProperty(name='Message', default="",update=updateNode)
	Key: StringProperty(name='Key', default="DefaultKey",update=updateNode)
	OpenURL: BoolProperty(name="Open URL", default=False, update=updateNode)
	Run: BoolProperty(name="Run", default=False, update=updateNode)


	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Client')
		self.inputs.new('SvStringsSocket', 'Stream')
		self.inputs.new('SvStringsSocket', 'Branch')
		self.inputs.new('SvStringsSocket', 'Description').prop_name='Description'
		self.inputs.new('SvStringsSocket', 'Message').prop_name='Message'
		self.inputs.new('SvStringsSocket', 'Key').prop_name='Key'
		self.inputs.new('SvStringsSocket', 'Object')
		self.inputs.new('SvStringsSocket', 'Open URL').prop_name = 'OpenURL'
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
		objectList = self.inputs['Object'].sv_get(deepcopy=True)
		openURLList = self.inputs['Open URL'].sv_get(deepcopy=True)
		runList = self.inputs['Run'].sv_get(deepcopy=True)
		clientList = flatten(clientList)
		streamList = flatten(streamList)
		branchList = flatten(branchList)
		descriptionList = flatten(descriptionList)
		messageList = flatten(messageList)
		keyList = flatten(keyList)
		objectList = flatten(objectList)
		openURLList = flatten(openURLList)
		runList = flatten(runList)
		inputs = [clientList, streamList, branchList, descriptionList, messageList, keyList, objectList, openURLList, runList]
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
    bpy.utils.register_class(SvSpeckleSendObject)

def unregister():
    bpy.utils.unregister_class(SvSpeckleSendObject)
