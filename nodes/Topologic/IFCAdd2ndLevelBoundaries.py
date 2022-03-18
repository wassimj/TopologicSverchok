
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
    self.inputs.new('SvStringsSocket', 'Building elements')
    self.inputs.new('SvStringsSocket', 'Unconnected faces')

    self.outputs.new('SvStringsSocket', 'IFC')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    input_ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    top_building_element_cellss = self.inputs['Building elements'].sv_get(deepcopy=False)[0]
    input_top_building_facess = self.inputs['Unconnected faces'].sv_get(deepcopy=False)[0]

    output_ifc_files = []
    for ifc_file, top_building_element_cells, top_building_faces in zip(input_ifc_files, top_building_element_cellss, input_top_building_facess):
      for ifc_space_boundary in ifc_file.by_type("IfcRelSpaceBoundary"):
        ifc_file.remove(ifc_space_boundary)

      for cell in top_building_element_cells:
        ifc_building_element = ifc_file.by_guid(topologic_lib.getDictionary(cell, "IfcBuildingElement"))
        faces = [ face for face in top_building_faces if topologic_lib.getDictionary(face, "IfcBuildingElement") == ifc_building_element.GlobalId ]

        top_opening_elements = []
        for ifc_rel_voids_element in ifc_building_element.HasOpenings:
          ifc_opening_element = ifc_rel_voids_element.RelatedOpeningElement
          top_opening_element = ifc_topologic.getIfcProductCell(ifc_opening_element)
          if not ifc_opening_element.HasFillings:
            continue

          topologic_lib.setDictionary(top_opening_element, "IfcElement", ifc_opening_element.HasFillings[0].RelatedBuildingElement.GlobalId)
          top_opening_elements.append(top_opening_element)

        space_boundary_2bs = [ face for face in faces ]
        thk, thk_area, dists = None, 0.0, {}
        for face_index, face in enumerate(faces):
          normal = topologic.FaceUtility.NormalAtParameters(face, 0.5, 0.5)
          n = np.array([normal[0], normal[1], normal[2]])
          point = topologic.FaceUtility.VertexAtParameters(face, 0.5, 0.5)
          p = np.array([point.X(), point.Y(), point.Z()])
          d = np.dot(n, p)

          ifc_space = ifc_file.by_guid(topologic_lib.getDictionary(face, "IfcSpace"))
          for other_face_index in range(face_index+1, len(faces)):
            other_face = faces[other_face_index]
            other_normal = topologic.FaceUtility.NormalAtParameters(other_face, 0.5, 0.5)
            other_n = np.array([other_normal[0], other_normal[1], other_normal[2]])
            if np.dot(n, other_n) + 1 > 1e-6:
              continue

            other_point = topologic.FaceUtility.VertexAtParameters(other_face, 0.5, 0.5)
            other_p = np.array([other_point.X(), other_point.Y(), other_point.Z()])
            dist = -np.dot(n, other_p) + d
            if dist < 1e-6:
              continue

            top_space_boundary = topologic_lib.boolean(face, topologic.TopologyUtility.Translate(other_face, dist*normal[0], dist*normal[1], dist*normal[2]), "Intersect")
            if top_space_boundary is None:
              continue

            top_space_boundary = topologic_lib.getSubTopologies(top_space_boundary, topologic.Face)
            if not top_space_boundary:
              continue

            top_space_boundary = top_space_boundary[0]
            other_ifc_space = ifc_file.by_guid(topologic_lib.getDictionary(faces[other_face_index], "IfcSpace"))
            ifc_rel_space_boundary, space_boundary_2bs[face_index] = ifc_topologic.createRelSpaceBoundary2ndLevel(
              ifc_file, top_space_boundary, True, ifc_space, other_ifc_space, ifc_building_element, space_boundary_2bs[face_index])
            other_top_space_boundary = topologic_lib.getSubTopologies(topologic.TopologyUtility.Translate(top_space_boundary, -dist*normal[0], -dist*normal[1],-dist*normal[2]), topologic.Face)[0]
            other_ifc_rel_space_boundary, space_boundary_2bs[other_face_index] = ifc_topologic.createRelSpaceBoundary2ndLevel(
              ifc_file, other_top_space_boundary, False, other_ifc_space, ifc_space, ifc_building_element, space_boundary_2bs[other_face_index])

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

        for key in dists:
          if abs(dists[key] - thk) < 0.01:
            continue

          ifc_rel_space_boundary = ifc_file.by_guid(key)
          ifc_rel_space_boundary.Description = "2b"
          ifc_rel_space_boundary.InternalOrExternalBoundary = "EXTERNAL"
          ifc_rel_space_boundary.CorrespondingBoundary = None

        for face, space_boundary_2b in zip(faces, space_boundary_2bs):
          ifc_space = ifc_file.by_guid(topologic_lib.getDictionary(face, "IfcSpace"))
          if ifc_space is not None:
            vs, fs = topologic_lib.meshData(space_boundary_2b)
            for f in fs:
              ifc_topologic.createRelSpaceBoundary(ifc_file, "IfcRelSpaceBoundary2ndLevel", "2b", ifc_space, ifc_building_element, vs, f[::-1], "EXTERNAL")
      output_ifc_files.append(ifc_file)

    self.outputs['IFC'].sv_set([output_ifc_files])

def register():
  bpy.utils.register_class(SvIFCAdd2ndLevelBoundaries)

def unregister():
  bpy.utils.unregister_class(SvIFCAdd2ndLevelBoundaries)
