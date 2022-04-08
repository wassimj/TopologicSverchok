
import bpy
from sverchok.node_tree import SverchCustomTreeNode
from . import topologic_lib
import topologic
from . import ifc_topologic
import ifcopenshell

class SvIFCCreateSpaces(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Create IFC Space
  Tooltip: Creates IFC spaces from unconnected faces of IfcBuildingElements
  """
  bl_idname = 'SvIFCCreateSpaces'
  bl_label = 'IFC.CreateSpaces'

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'IFC')
    self.inputs.new('SvStringsSocket', 'Building topology')

    self.outputs.new('SvStringsSocket', 'IFC')
    self.outputs.new('SvStringsSocket', 'Building topology')
    self.outputs.new('SvStringsSocket', 'Spaces')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    input_ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    input_top_building_cell_complexs = self.inputs['Building topology'].sv_get(deepcopy=False)[0]

    output_ifc_files, output_top_building_cell_complexs, top_space_cellss = [], [], []
    for ifc_file, top_building_cell_complex in zip(input_ifc_files, input_top_building_cell_complexs):
      top_space_cells = []
      
      for ifc_space in ifc_file.by_type("IfcSpace"):
        ifc_file.remove(ifc_space)

      body_context = next((item  for item  in ifc_file.by_type("IfcGeometricRepresentationSubContext") if item.ContextIdentifier == "Body"), None)
      if body_context is None:
        parent_context = next((item  for item  in ifc_file.by_type("IfcGeometricRepresentationContext") if item.ContextType == "Model"), None)
        body_context = ifc_file.createIfcGeometricRepresentationSubContext("Body", "Model", None, None, None, None, parent_context, None, "MODEL_VIEW", None)
      
      sink_faces = {}
      for cell in topologic_lib.getSubTopologies(top_building_cell_complex, topologic.Cell):
        global_id = topologic_lib.getDictionary(cell, "IfcBuildingElement")
        sink_faces[global_id] = [ face for face in topologic_lib.getSubTopologies(cell, topologic.Face) if topologic_lib.getDictionary(face, "IfcBuildingElement") is not None ]

      cells, shells = [], []
      ext_boundary = top_building_cell_complex.ExternalBoundary()
      for shell in topologic_lib.getSubTopologies(ext_boundary, topologic.Shell):
        cell = topologic.Cell.ByShell(shell)
        if topologic.CellUtility.Volume(cell) < 1e-6:
          continue
        
        cells.append(cell)
        shells.append(shell)
      
      sorted_indices = [ i[0] for i in sorted(enumerate(cells), key=lambda x: topologic.CellUtility.Volume(x[1])) ]
      ifc_topologic.assignRepresentation(cells[sorted_indices[-1]], ifc_file, ifc_file.by_type('IfcBuilding')[0])
      for index_cell in sorted_indices[:-1]:
        top_space_cell = cells[index_cell]
        faces = topologic_lib.getSubTopologies(shells[index_cell], topologic.Face) 
        
        ifc_space = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class="IfcSpace")
        ifc_space.CompositionType = "ELEMENT"
        ifc_space.PredefinedType = "INTERNAL"
        ifc_space.Name = "Space " + str(len(ifc_file.by_type('IfcSpace')) - 1)
        ifc_storey = ifc_topologic.getFacesStorey(faces, ifc_file)
        ifcopenshell.api.run("aggregate.assign_object", ifc_file, product=ifc_space, relating_object=ifc_storey)
        ifc_topologic.assignRepresentation(top_space_cell, ifc_file, ifc_space)
        for face in faces:
          global_id = topologic_lib.getDictionary(face, "IfcBuildingElement")
          ifc_building_element = ifc_file.by_guid(global_id)
          vs, fs = topologic_lib.meshData(face)
          ifc_topologic.createRelSpaceBoundary(ifc_file, "IfcRelSpaceBoundary1stLevel", None, ifc_space, ifc_building_element, vs, fs[0][::-1], "EXTERNAL")
          
          vertex = topologic.FaceUtility.InternalVertex(face, 1e-3)
          for sink_face in sink_faces[global_id]:
            if topologic.FaceUtility.IsInside(sink_face, vertex, 1e-4):
              topologic_lib.setDictionary(sink_face, "IfcSpace", ifc_space.GlobalId)
              sink_faces[global_id].remove(sink_face)
              break
        top_space_cells.append(top_space_cell)
      output_ifc_files.append(ifc_file)
      output_top_building_cell_complexs.append(top_building_cell_complex)
      top_space_cellss.append(top_space_cells)

    self.outputs['IFC'].sv_set([output_ifc_files])
    self.outputs['Building topology'].sv_set([output_top_building_cell_complexs])
    self.outputs['Spaces'].sv_set([top_space_cellss])

def register():
  bpy.utils.register_class(SvIFCCreateSpaces)

def unregister():
  bpy.utils.unregister_class(SvIFCCreateSpaces)
