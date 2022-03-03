
import bpy
from sverchok.node_tree import SverchCustomTreeNode
from . import topologic_lib
from . import ifc_topologic
import topologic

class SvIFCConnectBuildingElements(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Connect building elements
  Tooltip: Add IfcRelConnectsElements that connect IfcBuildingElements
  """
  bl_idname = 'SvIFCConnectBuildingElements'
  bl_label = 'IFC.ConnectBuildingElements'

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'IFC')
    self.inputs.new('SvStringsSocket', 'Building elements')
    self.inputs.new('SvStringsSocket', 'Building topology')

    self.outputs.new('SvStringsSocket', 'IFC')
    self.outputs.new('SvStringsSocket', 'Building topology')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    input_ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    top_building_element_cellss = self.inputs['Building elements'].sv_get(deepcopy=False)[0]
    input_top_building_cell_complexs = self.inputs['Building topology'].sv_get(deepcopy=False)[0]

    output_ifc_files, output_top_building_cell_complexs = [], []
    for ifc_file, top_building_element_cells, top_building_cell_complex in zip(input_ifc_files, top_building_element_cellss, input_top_building_cell_complexs):
      for top_building_element_cell in top_building_element_cells:
        ifc_building_element = ifc_file.by_guid(topologic_lib.getDictionary(top_building_element_cell, "IfcBuildingElement"))

        int_bounds = []
        top_building_element_cell.InternalBoundaries(int_bounds)

        for shell in int_bounds:
          vs, fs = topologic_lib.meshData(shell)
          for f in fs:
            ifc_topologic.createRelConnectsElements(ifc_file, ifc_building_element, ifc_building_element, vs, f)

      for face in topologic_lib.getSubTopologies(top_building_cell_complex, topologic.Face):
        ajacent_cells = []
        _ = topologic.FaceUtility.AdjacentCells(face, top_building_cell_complex, ajacent_cells)

        global_id = topologic_lib.getDictionary(ajacent_cells[0], "IfcBuildingElement")
        ifc_building_element = ifc_file.by_guid(global_id)
        if len(ajacent_cells) > 1:
          other_global_id = topologic_lib.getDictionary(ajacent_cells[1], "IfcBuildingElement")
          other_ifc_building_element = ifc_file.by_guid(other_global_id)
          vs, fs = topologic_lib.meshData(face)
          for f in fs:
            ifc_topologic.createRelConnectsElements(ifc_file, ifc_building_element, other_ifc_building_element, vs, f)
        else:
          topologic_lib.setDictionary(face, "IfcBuildingElement", global_id)

      output_ifc_files.append(ifc_file)
      output_top_building_cell_complexs.append(top_building_cell_complex)

    self.outputs['IFC'].sv_set([output_ifc_files])
    self.outputs['Building topology'].sv_set([output_top_building_cell_complexs])

def register():
    bpy.utils.register_class(SvIFCConnectBuildingElements)

def unregister():
    bpy.utils.unregister_class(SvIFCConnectBuildingElements)
