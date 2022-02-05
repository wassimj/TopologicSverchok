
import bpy
from sverchok.node_tree import SverchCustomTreeNode
from . import topologic_lib
import numpy as np
from scipy.sparse.csgraph import connected_components
import topologic
import ifcopenshell
from . import ifc_topologic

class SvIFCCreateSpaces(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Create IFC Space
  Tooltip: Creates IFC spaces from unconnected faces of IfcBuildingElements
  """
  bl_idname = 'SvIFCCreateSpaces'
  bl_label = 'IFC.CreateSpaces'

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'IFC')
    self.inputs.new('SvStringsSocket', 'Building elements')
    self.inputs.new('SvStringsSocket', 'Building elements graph')
    self.inputs.new('SvStringsSocket', 'Unconnected faces')

    self.outputs.new('SvStringsSocket', 'IFC')
    self.outputs.new('SvStringsSocket', 'Unconnected faces')
    self.outputs.new('SvStringsSocket', 'Spaces')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    input_ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    top_building_element_cellss = self.inputs['Building elements'].sv_get(deepcopy=False)[0]
    building_elements_graphs = self.inputs['Building elements graph'].sv_get(deepcopy=False)[0]
    input_top_building_facess = self.inputs['Unconnected faces'].sv_get(deepcopy=False)[0]

    output_ifc_files, output_top_building_facess, top_spacess = [], [], []
    for ifc_file, top_building_element_cells, building_elements_graph, top_building_faces in zip(input_ifc_files, top_building_element_cellss, building_elements_graphs, input_top_building_facess):
      top_spaces = []

      body_context = next((item  for item  in ifc_file.by_type("IfcGeometricRepresentationSubContext") if item.ContextIdentifier == "Body"), None)
      if body_context is None:
        parent_context = next((item  for item  in ifc_file.by_type("IfcGeometricRepresentationContext") if item.ContextType == "Model"), None)
        body_context = ifc_file.createIfcGeometricRepresentationSubContext("Body", "Model", None, None, None, None, parent_context, None, "MODEL_VIEW", None)

      ifc_building_elements_ids = [ topologic_lib.getDictionary(top_building_element_cell, "IfcBuildingElement") for top_building_element_cell in top_building_element_cells]
      face_building_element_indices = [ ifc_building_elements_ids.index(topologic_lib.getDictionary(top_building_face, "IfcBuildingElement")) for top_building_face in top_building_faces]
      building_faces_graph = np.zeros((len(top_building_faces), len(top_building_faces)), dtype=np.bool)
      for face_index, top_building_face in enumerate(top_building_faces):
        building_element_index = face_building_element_indices[face_index]
        for other_face_index in range(face_index+1, len(top_building_faces)):
          if not building_elements_graph[building_element_index, face_building_element_indices[other_face_index]]:
            continue

          other_top_building_face = top_building_faces[other_face_index]
          if topologic_lib.boolean(top_building_face, other_top_building_face, "Intersect") is None:
            continue

          building_faces_graph[face_index,other_face_index] = 1
      n_components, labels = connected_components(csgraph=building_faces_graph, directed=False, return_labels=True)

      cells = [ topologic.Cell.ByFaces([ face for j, face in enumerate(top_building_faces) if labels[j] == i ], 1e-4) for i in range(n_components) ]
      sorted_indices = [ i[0] for i in sorted(enumerate(cells), key=lambda x: topologic.CellUtility.Volume(x[1])) ]
      for index_cell in sorted_indices[:-1]:
        top_space = cells[index_cell]
        faces = [ face for j, face in enumerate(top_building_faces) if labels[j] == index_cell ]

        ifc_space = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class="IfcSpace")
        ifc_space.CompositionType = "ELEMENT"
        ifc_space.PredefinedType = "INTERNAL"
        ifc_space.Name = "Space " + str(len(ifc_file.by_type('IfcSpace')) - 1)
        ifcopenshell.api.run("aggregate.assign_object", ifc_file, product=ifc_space, relating_object=ifc_topologic.getFacesStorey(faces, ifc_file))

        vs, fs = topologic_lib.meshData(top_space)
        o, z = None, None
        for v in vs:
          if z is None or v[-1] < z:
            o, z = v, v[-1]
        space_matrix = ifcopenshell.util.placement.a2p(o, np.array([0,0,1]), np.array([1,0,0]))
        point_list = ifc_file.createIfcCartesianPointList3D([ np.linalg.solve(space_matrix, np.append(v,1))[:-1].tolist() for v in vs ])
        indexed_faces = [ ifc_file.createIfcIndexedPolygonalFace([ index + 1 for index in f]) for f in fs ]
        representation = ifc_file.createIfcPolygonalFaceSet(point_list, None, indexed_faces, None)
        shape = ifc_file.createIfcShapeRepresentation(body_context, body_context.ContextIdentifier, "Tessellation", [representation])
        ifcopenshell.api.run("geometry.assign_representation", ifc_file, product=ifc_space, representation=shape)
        ifcopenshell.api.run("geometry.edit_object_placement", ifc_file, product=ifc_space, matrix=space_matrix)

        for face in faces:
          ifc_building_element = ifc_file.by_guid(topologic_lib.getDictionary(face, "IfcBuildingElement"))
          vs, fs = topologic_lib.meshData(face)
          ifc_topologic.createRelSpaceBoundary(ifc_file, "IfcRelSpaceBoundary1stLevel", None, ifc_space, ifc_building_element, vs, fs[0][::-1], "EXTERNAL")

          topologic_lib.setDictionary(face, "IfcSpace", ifc_space.GlobalId)
        topologic_lib.setDictionary(top_space, "IfcSpace", ifc_space.GlobalId)
        top_spaces.append(top_space)
      output_ifc_files.append(ifc_file)
      output_top_building_facess.append(top_building_faces)
      top_spacess.append(top_spaces)

    self.outputs['IFC'].sv_set([output_ifc_files])
    self.outputs['Unconnected faces'].sv_set([output_top_building_facess])
    self.outputs['Spaces'].sv_set([top_spacess])

def register():
  bpy.utils.register_class(SvIFCCreateSpaces)

def unregister():
  bpy.utils.unregister_class(SvIFCCreateSpaces)
