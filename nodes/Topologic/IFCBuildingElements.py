
import bpy
from sverchok.node_tree import SverchCustomTreeNode
from . import ifc_topologic
from . import topologic_lib

class SvIFCBuildingElements(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Building elements cells
  Tooltip: Get Cells from IfcBuildingElements
  """
  bl_idname = 'SvIFCBuildingElements'
  bl_label = 'IFC.BuildingElements'

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'IFC')

    self.outputs.new('SvStringsSocket', 'Building elements')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]

    top_building_element_cellss = []
    for ifc_file in ifc_files:
      top_building_element_cells = []
      for ifc_building_element in ifc_file.by_type("IfcBuildingElement"):
        if ifc_building_element.is_a("IfcSlab"):
          if not any([ ifc_building_element.PredefinedType == ifc_slab_type  for ifc_slab_type in ["FLOOR", "ROOF", "BASESLAB", "NOTDEFINED"] ]):
            continue
        elif ifc_building_element.is_a("IfcWall"):
          if not any([ ifc_building_element.PredefinedType == ifc_slab_type  for ifc_slab_type in ["SOLIDWALL", "STANDARD", "POLYGONAL", "NOTDEFINED"] ]):
            continue
        else:
          continue

        top_building_element_cell = ifc_topologic.getIfcProductCell(ifc_building_element)
        topologic_lib.setDictionary(top_building_element_cell, "IfcBuildingElement", ifc_building_element.GlobalId)
        top_building_element_cells.append(top_building_element_cell)
      top_building_element_cellss.append(top_building_element_cells)

    self.outputs['Building elements'].sv_set([top_building_element_cellss])

def register():
    bpy.utils.register_class(SvIFCBuildingElements)

def unregister():
    bpy.utils.unregister_class(SvIFCBuildingElements)
