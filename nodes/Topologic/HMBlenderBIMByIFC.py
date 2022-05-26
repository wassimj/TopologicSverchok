import bpy
import re
import logging
from sverchok.node_tree import SverchCustomTreeNode
from blenderbim.bim import import_ifc
from blenderbim.bim.ifc import IfcStore

class SvHMBlenderBIMByIFC(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Load an IFC file object in BlenderBIM
  Tooltip: Load an IFC file object in BlenderBIM
  """
  bl_idname = 'SvHMBlenderBIMByIFC'
  bl_label = 'Homemaker.BlenderBIMByIFC'

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'IFC')
    self.outputs.new('SvStringsSocket', 'Status')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    ifc_file = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    if IfcStore.file:
        IfcStore.purge()
    IfcStore.file = ifc_file

    # delete any IfcProject/* collections
    for collection in bpy.data.collections:
      if re.match("^IfcProject/", collection.name):
        delete_collection(collection)

    # (re)build blender collections and geometry from IfcStore
    ifc_import_settings = import_ifc.IfcImportSettings.factory(
        bpy.context, "", logging.getLogger("ImportIFC")
    )
    ifc_importer = import_ifc.IfcImporter(ifc_import_settings)
    ifc_importer.execute()

    self.outputs['Status'].sv_set([True])

def delete_collection(blender_collection):
    for obj in blender_collection.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(blender_collection)
    for collection in bpy.data.collections:
        if not collection.users:
            bpy.data.collections.remove(collection)

def register():
    bpy.utils.register_class(SvHMBlenderBIMByIFC)

def unregister():
    bpy.utils.unregister_class(SvHMBlenderBIMByIFC)
