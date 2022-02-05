
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
    self.outputs.new('SvStringsSocket', 'Building elements graph')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    top_building_element_cellss = self.inputs['Building elements'].sv_get(deepcopy=False)[0]

    clashess, building_elements_graphs = [], []
    for ifc_file, top_building_element_cells in zip(ifc_files, top_building_element_cellss):
      clashes = []
      building_elements_graph = np.zeros((len(top_building_element_cells), len(top_building_element_cells)), dtype=np.bool)

      top_building_element_bounding_boxs = [ topologic_lib.getBoundingBox(building_element_cell) for building_element_cell in top_building_element_cells ]
      for building_element_index, building_element_cell in enumerate(top_building_element_cells):
        top_building_element_bounding_box = top_building_element_bounding_boxs[building_element_index]
        for other_building_element_index in range(building_element_index+1, len(top_building_element_cells)):
          if not topologic_lib.doBoundingBoxIntersect(top_building_element_bounding_box, top_building_element_bounding_boxs[other_building_element_index]):
            continue

          other_building_element_cell = top_building_element_cells[other_building_element_index]
          intersection = topologic_lib.boolean(building_element_cell, other_building_element_cell, "Intersect")
          if intersection is None:
            continue

          intersection_cells = topologic_lib.getSubTopologies(intersection, topologic.Cell)
          if len(intersection_cells) > 0:
            clashes.append([building_element_cell, other_building_element_cell])
          building_elements_graph[building_element_index,other_building_element_index] = 1
      building_elements_graph += building_elements_graph.T + np.eye(len(top_building_element_cells), dtype=np.bool)

      clashess.append(clashes)
      building_elements_graphs.append(building_elements_graph)

    self.outputs['Clashes'].sv_set([clashess])
    self.outputs['Building elements graph'].sv_set([building_elements_graphs])

def register():
    bpy.utils.register_class(SvIFCClashDetection)

def unregister():
    bpy.utils.unregister_class(SvIFCClashDetection)
