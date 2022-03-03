
import bpy
from sverchok.node_tree import SverchCustomTreeNode
import numpy as np
from . import topologic_lib
import topologic

class SvIFCClashDetection(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Clash detection
  Tooltip: Detect clashes between building elements
  """
  bl_idname = 'SvIFCClashDetection'
  bl_label = 'IFC.ClashDetection'

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'IFC')
    self.inputs.new('SvStringsSocket', 'Building elements')

    self.outputs.new('SvStringsSocket', 'Clashes')
    self.outputs.new('SvStringsSocket', 'Building topology')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    top_building_element_cellss = self.inputs['Building elements'].sv_get(deepcopy=False)[0]

    clashess, top_building_cell_complexs = [], []
    for ifc_file, top_building_element_cells in zip(ifc_files, top_building_element_cellss):
      top_building_cell_complex = topologic.CellComplex.ByCells(top_building_element_cells)

      clashes = []
      for sink in topologic_lib.getSubTopologies(top_building_cell_complex, topologic.Cell):
        vertex = topologic.CellUtility.InternalVertex(sink, 1e-3)

        cells = []
        for source in top_building_element_cells:
          if topologic.CellUtility.Contains(source, vertex, 1e-4) == 0:
            cells.append(source)

        if len(cells) > 1:
          clashes.append([sink] + cells)
        else:
          global_id = topologic_lib.getDictionary(cells[0], "IfcBuildingElement")
          topologic_lib.setDictionary(sink, "IfcBuildingElement", global_id)

      clashess.append(clashes)
      top_building_cell_complexs.append(top_building_cell_complex)

    self.outputs['Clashes'].sv_set([clashess])
    self.outputs['Building topology'].sv_set([top_building_cell_complexs])

def register():
    bpy.utils.register_class(SvIFCClashDetection)

def unregister():
    bpy.utils.unregister_class(SvIFCClashDetection)
