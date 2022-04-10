
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from honeybee.model import Model
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.construction.opaque import OpaqueConstruction
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.pointvector import Point3D
from honeybee.face import Face
from honeybee.aperture import Aperture
from honeybee.door import Door
from honeybee.room import Room
from honeybee.boundarycondition import boundary_conditions
import ifcopenshell
import numpy as np
from . import ifc_topologic
import json

class SvIFCExportToHBJSON(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Export analytical model to HBJSON
  Tooltip: Exports the analytical model in IFC to HBJSON
  """
  bl_idname = 'SvIFCExportToHBJSON'
  bl_label = 'IFC.ExportToHBJSON'
  FilePath: StringProperty(name="File Path", default="", subtype="FILE_PATH")

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'IFC')
    self.inputs.new('SvStringsSocket', 'Offset')
    self.inputs.new('SvStringsSocket', 'File Path').prop_name='FilePath'

    self.outputs.new('SvStringsSocket', 'HBJSON')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    offsets = self.inputs['Offset'].sv_get(deepcopy=False)[0]
    file_paths = self.inputs['File Path'].sv_get(deepcopy=False)[0]

    hbjsons = []
    for idx, ifc_file in enumerate(ifc_files):
      file_path = file_paths[idx]
      offset = offsets[idx]

      id2hb = {}

      hb_model = Model("Model")

      for ifc_material_layer in ifc_file.by_type('IfcMaterialLayer'):
        if not ifc_material_layer.ToMaterialLayerSet:
          continue

        material_id = ifc_material_layer.id()
        thickness = float(ifc_material_layer.LayerThickness)
        hb_material = EnergyMaterial(str(material_id), thickness, 0.1, 0.1, 1400)
        hb_material.display_name = ifc_material_layer.Material.Name + " - " + str(ifc_material_layer.LayerThickness)
        id2hb[material_id] = hb_material

      for ifc_material_layer_set in ifc_file.by_type('IfcMaterialLayerSet'):
        construction_id = ifc_material_layer_set.id()
        layers = [ id2hb[ifc_material_layer.id()] for ifc_material_layer in ifc_material_layer_set.MaterialLayers ]
        hb_construction = OpaqueConstruction(str(construction_id), layers)
        hb_construction.display_name = ifc_material_layer_set.LayerSetName
        id2hb[construction_id] = hb_construction

      for ifc_building_storey in ifc_file.by_type('IfcBuildingStorey'):
        if not ifc_building_storey.IsDecomposedBy:
          continue

        ifc_spaces = [ x for x in ifc_building_storey.IsDecomposedBy[0].RelatedObjects if x.is_a("IfcSpace") ]
        if not ifc_spaces:
          continue

        for ifc_space in ifc_spaces:
          space_matrix = ifcopenshell.util.placement.get_local_placement(ifc_space.ObjectPlacement)

          faces = []
          for ifc_rel_space_boundary in ifc_space.BoundedBy:
            if ifc_rel_space_boundary.ParentBoundary is not None:
              continue

            surface_id = ifc_rel_space_boundary.id()
            vertices = [ (space_matrix @ np.append(v,1))[:-1] for v in ifc_topologic.getLocalVertices(ifc_rel_space_boundary, 0.0) ]
            geom = Face3D([ Point3D.from_array(v) for v in vertices ])
            hb_face = Face(str(surface_id), geom)
            hb_face.display_name = ifc_rel_space_boundary.Name

            ifc_building_element = ifc_rel_space_boundary.RelatedBuildingElement
            if ifc_building_element is not None:
              for ifc_rel_associates in ifc_building_element.HasAssociations:
                if not ifc_rel_associates.is_a("IfcRelAssociatesMaterial"):
                  continue

                ifc_material = ifc_rel_associates.RelatingMaterial
                if ifc_material.is_a('IfcMaterialLayerSetUsage'):
                  ifc_material = ifc_material.ForLayerSet
                elif not ifc_material.is_a('IfcMaterialLayerSet'):
                  continue

                hb_face.properties.energy.construction = id2hb[ifc_material.id()]
                break

            for ifc_inner_boundary in ifc_rel_space_boundary.InnerBoundaries:
              if ifc_inner_boundary.ParentBoundary != ifc_rel_space_boundary:
                continue

              sub_surface_id = ifc_inner_boundary.id()
              name = ifc_inner_boundary.Name
              vertices = [ (space_matrix @ np.append(v,1))[:-1] for v in ifc_topologic.getLocalVertices(ifc_inner_boundary, offset) ]
              geom = Face3D([ Point3D.from_array(v) for v in vertices ])
              if ifc_inner_boundary.RelatedBuildingElement.is_a("IfcWindow"):
                hb_aperture = Aperture(str(sub_surface_id), geom)
                hb_face.add_aperture(hb_aperture)
                id2hb[sub_surface_id] = hb_aperture
              elif ifc_inner_boundary.RelatedBuildingElement.is_a("IfcDoor"):
                hb_door = Door(str(sub_surface_id), geom)
                hb_face.add_door(hb_door)
                id2hb[sub_surface_id] = hb_door
              id2hb[sub_surface_id].display_name = ifc_inner_boundary.Name

            faces.append(hb_face)
            id2hb[surface_id] = hb_face

          space_id = ifc_space.id()
          hb_room = Room(str(space_id), faces)
          hb_room.display_name = ifc_space.Name
          hb_room.story = ifc_building_storey.Name

          for hb_face in hb_room.faces:
            ifc_rel_space_boundary = ifc_file.by_id(int(hb_face.identifier))

            if ifc_rel_space_boundary.CorrespondingBoundary is None:
              if ifc_rel_space_boundary.Description == "2a":
                hb_face.boundary_condition = boundary_conditions.outdoors
              elif ifc_rel_space_boundary.Description == "2b":
                hb_face.boundary_condition = boundary_conditions.adiabatic
            else:
              adjacent_surface_id = ifc_rel_space_boundary.CorrespondingBoundary.id()
              if adjacent_surface_id in id2hb:
                hb_face.boundary_condition = boundary_conditions.surface(id2hb[adjacent_surface_id])
                id2hb[adjacent_surface_id].boundary_condition = boundary_conditions.surface(hb_face)

                for ifc_inner_boundary in ifc_rel_space_boundary.InnerBoundaries:
                  if ifc_inner_boundary.ParentBoundary != ifc_rel_space_boundary:
                    continue

                  hb_sub_surface = id2hb[ifc_inner_boundary.id()]
                  hb_adjacent_sub_surface = id2hb[ifc_inner_boundary.CorrespondingBoundary.id()]
                  hb_sub_surface.boundary_condition = boundary_conditions.surface(hb_adjacent_sub_surface, True)
                  hb_adjacent_sub_surface.boundary_condition = boundary_conditions.surface(hb_sub_surface, True)
              else:
                hb_face.boundary_condition = boundary_conditions.outdoors

          hb_model.add_room(hb_room)

      f = open(file_path, "w")
      json.dump(hb_model.to_dict(), f, indent=4)
      f.close()

      hbjsons.append(hb_model)

    self.outputs['HBJSON'].sv_set([hbjsons])

def register():
  bpy.utils.register_class(SvIFCExportToHBJSON)

def unregister():
  bpy.utils.unregister_class(SvIFCExportToHBJSON)
