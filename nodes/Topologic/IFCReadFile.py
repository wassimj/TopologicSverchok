
import bpy
from sverchok.node_tree import SverchCustomTreeNode
import ifcopenshell

class SvIFCReadFile(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Read IFC file
  Tooltip: Read an IFC file from path
  """
  bl_idname = 'SvIFCReadFile'
  bl_label = 'IFC.ReadFile'

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'File Path')

    self.outputs.new('SvStringsSocket', 'IFC')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    file_paths = self.inputs['File Path'].sv_get(deepcopy=False)[0]

    ifc_files = []
    for file_path in file_paths:
      ifc_files.append(ifcopenshell.open(file_path))

    self.outputs['IFC'].sv_set([ifc_files])

def register():
    bpy.utils.register_class(SvIFCReadFile)

def unregister():
    bpy.utils.unregister_class(SvIFCReadFile)
