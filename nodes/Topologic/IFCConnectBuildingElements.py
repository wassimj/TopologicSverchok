
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
    self.inputs.new('SvStringsSocket', 'Building elements graph')

    self.outputs.new('SvStringsSocket', 'IFC')
    self.outputs.new('SvStringsSocket', 'Unconnected faces')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    input_ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    top_building_element_cellss = self.inputs['Building elements'].sv_get(deepcopy=False)[0]
    building_elements_graphs = self.inputs['Building elements graph'].sv_get(deepcopy=False)[0]

    output_ifc_files, top_building_facess = [], []
    for ifc_file, top_building_element_cells, building_elements_graph in zip(input_ifc_files, top_building_element_cellss, building_elements_graphs):
      top_building_faces = []

      top_building_element_shells = [ building_element_cell.ExternalBoundary() for building_element_cell in top_building_element_cells ]
      for building_element_index, building_element_cell in enumerate(top_building_element_cells):
        ifc_building_element = ifc_file.by_guid(topologic_lib.getDictionary(building_element_cell, "IfcBuildingElement"))
        int_bounds = []
        building_element_cell.InternalBoundaries(int_bounds)
        for shell in int_bounds:
          vs, fs = topologic_lib.meshData(shell)
          for f in fs:
            ifc_topologic.createRelConnectsElements(ifc_file, ifc_building_element, ifc_building_element, vs, f)

        building_element_shell = top_building_element_shells[building_element_index]
        for other_building_element_index in range(building_element_index+1, len(top_building_element_cells)):
          if not building_elements_graph[building_element_index, other_building_element_index]:
            continue

          other_building_element_cell = top_building_element_cells[other_building_element_index]
          intersection = topologic_lib.boolean(building_element_shell, other_building_element_cell, "Intersect")
          vs, fs = topologic_lib.meshData(intersection)
          if len(fs) < 1:
            continue

          other_ifc_building_element = ifc_file.by_guid(topologic_lib.getDictionary(other_building_element_cell, "IfcBuildingElement"))
          for f in fs:
            ifc_topologic.createRelConnectsElements(ifc_file, ifc_building_element, other_ifc_building_element, vs, f)

          building_element_shell = topologic_lib.boolean(building_element_shell, intersection, "Difference")
          other_building_element_shell = top_building_element_shells[other_building_element_index]
          other_building_element_shell = topologic_lib.boolean(other_building_element_shell, intersection, "Difference")
          top_building_element_shells[other_building_element_index] = other_building_element_shell
        faces = topologic_lib.getSubTopologies(building_element_shell, topologic.Face)
        top_building_element_shells[building_element_index] = faces
        for face in faces:
          topologic_lib.setDictionary(face, "IfcBuildingElement", ifc_building_element.GlobalId)
        top_building_faces += faces
      output_ifc_files.append(ifc_file)
      top_building_facess.append(top_building_faces)

    self.outputs['IFC'].sv_set([output_ifc_files])
    self.outputs['Unconnected faces'].sv_set([top_building_facess])

def register():
    bpy.utils.register_class(SvIFCConnectBuildingElements)

def unregister():
    bpy.utils.unregister_class(SvIFCConnectBuildingElements)
