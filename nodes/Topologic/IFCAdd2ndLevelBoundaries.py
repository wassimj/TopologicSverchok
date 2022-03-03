
import bpy
from sverchok.node_tree import SverchCustomTreeNode
from . import topologic_lib
from . import ifc_topologic
import topologic
import numpy as np

class SvIFCAdd2ndLevelBoundaries(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Add 2nd level boundaries
  Tooltip: Remove 1st level boundaries and add 2nd level boundaries
  """
  bl_idname = 'SvIFCAdd2ndLevelBoundaries'
  bl_label = 'IFC.Add2ndLevelBoundaries'

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'IFC')
    self.inputs.new('SvStringsSocket', 'Building topology')

    self.outputs.new('SvStringsSocket', 'IFC')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    input_ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    input_top_building_cell_complexs = self.inputs['Building topology'].sv_get(deepcopy=False)[0]

    output_ifc_files = []
    for ifc_file, top_building_cell_complex in zip(input_ifc_files, input_top_building_cell_complexs):
      for ifc_rel_space_boundary in ifc_file.by_type("IfcRelSpaceBoundary"):
        ifc_file.remove(ifc_rel_space_boundary)

      for cell in topologic_lib.getSubTopologies(top_building_cell_complex, topologic.Cell):
        ifc_building_element = ifc_file.by_guid(topologic_lib.getDictionary(cell, "IfcBuildingElement"))

        connected_faces, unconnected_faces = [], []
        for face in topologic_lib.getSubTopologies(cell, topologic.Face):
          if topologic_lib.getDictionary(face, "IfcBuildingElement") is None:
            connected_faces.append(face)
          else:
            unconnected_faces.append(face)

        top_opening_elements = []
        for ifc_rel_voids_element in ifc_building_element.HasOpenings:
          ifc_opening_element = ifc_rel_voids_element.RelatedOpeningElement
          top_opening_element = ifc_topologic.getIfcProductCell(ifc_opening_element)
          if not ifc_opening_element.HasFillings:
            continue

          topologic_lib.setDictionary(top_opening_element, "IfcElement", ifc_opening_element.HasFillings[0].RelatedBuildingElement.GlobalId)
          top_opening_elements.append(top_opening_element)

        thk, thk_area, dists = None, 0.0, {}
        for face_index, face in enumerate(unconnected_faces):
          normal = topologic.FaceUtility.NormalAtParameters(face, 0.5, 0.5)
          ifc_space = ifc_file.by_guid(topologic_lib.getDictionary(face, "IfcSpace"))

          for other_face_index in range(face_index+1, len(unconnected_faces)):
            dist, top_space_boundary = topologic_lib.projectFace(face, unconnected_faces[other_face_index])
            if dist is None:
              continue

            other_ifc_space = ifc_file.by_guid(topologic_lib.getDictionary(unconnected_faces[other_face_index], "IfcSpace"))
            ifc_rel_space_boundary = ifc_topologic.createRelSpaceBoundary2ndLevel(
              ifc_file, top_space_boundary, True, ifc_space, other_ifc_space, ifc_building_element)
            other_top_space_boundary = topologic_lib.getSubTopologies(topologic.TopologyUtility.Translate(top_space_boundary, -dist*normal[0], -dist*normal[1],-dist*normal[2]), topologic.Face)[0]
            other_ifc_rel_space_boundary = ifc_topologic.createRelSpaceBoundary2ndLevel(
              ifc_file, other_top_space_boundary, False, other_ifc_space, ifc_space, ifc_building_element)

            area = topologic.FaceUtility.Area(top_space_boundary)
            if area > thk_area:
              thk, thk_area = dist, area
            if ifc_rel_space_boundary is not None:
              dists[ifc_rel_space_boundary.GlobalId] = dist
            if other_ifc_rel_space_boundary is not None:
              dists[other_ifc_rel_space_boundary.GlobalId] = dist

            if ifc_rel_space_boundary is not None and other_ifc_rel_space_boundary is not None:
              ifc_rel_space_boundary.CorrespondingBoundary = other_ifc_rel_space_boundary
              other_ifc_rel_space_boundary.CorrespondingBoundary = ifc_rel_space_boundary

            for top_opening_element in top_opening_elements:
              ifc_inner_boundary = ifc_topologic.createInnerBoundary(ifc_rel_space_boundary, top_opening_element, top_space_boundary, True, ifc_file)
              other_ifc_inner_boundary = ifc_topologic.createInnerBoundary(other_ifc_rel_space_boundary, top_opening_element, other_top_space_boundary, False, ifc_file)

              if ifc_inner_boundary is not None and other_ifc_inner_boundary is not None:
                ifc_inner_boundary.CorrespondingBoundary = other_ifc_inner_boundary
                other_ifc_inner_boundary.CorrespondingBoundary = ifc_inner_boundary

          if ifc_space is not None:
            for connected_face in connected_faces:
              dist, top_space_boundary = topologic_lib.projectFace(face, connected_face)
              if dist is None:
                continue

              vs, fs = topologic_lib.meshData(top_space_boundary)
              for f in fs:
                ifc_topologic.createRelSpaceBoundary(ifc_file, "IfcRelSpaceBoundary2ndLevel", "2b", ifc_space, ifc_building_element, vs, f[::-1], "NOTDEFINED")

        for key in dists:
          if abs(dists[key] - thk) < 0.01:
            continue

          ifc_rel_space_boundary = ifc_file.by_guid(key)
          ifc_rel_space_boundary.Description = "2b"
          ifc_rel_space_boundary.InternalOrExternalBoundary = "EXTERNAL"
          ifc_rel_space_boundary.CorrespondingBoundary = None
      output_ifc_files.append(ifc_file)

    self.outputs['IFC'].sv_set([output_ifc_files])

def register():
  bpy.utils.register_class(SvIFCAdd2ndLevelBoundaries)

def unregister():
  bpy.utils.unregister_class(SvIFCAdd2ndLevelBoundaries)
