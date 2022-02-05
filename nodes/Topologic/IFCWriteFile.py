
import bpy
from sverchok.node_tree import SverchCustomTreeNode

class SvIFCWriteFile(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Write IFC file
  Tooltip: Write an IFC file from path
  """
  bl_idname = 'SvIFCWriteFile'
  bl_label = 'IFC.WriteFile'

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'IFC')
    self.inputs.new('SvStringsSocket', 'File Path')

    self.outputs.new('SvStringsSocket', 'Status')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    file_paths = self.inputs['File Path'].sv_get(deepcopy=False)[0]

    for ifc_file, file_path in zip(ifc_files, file_paths):
      ifc_file.write(file_path)

    self.outputs['Status'].sv_set([True])

def register():
    bpy.utils.register_class(SvIFCWriteFile)

def unregister():
    bpy.utils.unregister_class(SvIFCWriteFile)
