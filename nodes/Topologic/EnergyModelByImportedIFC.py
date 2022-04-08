
import bpy
from sverchok.node_tree import SverchCustomTreeNode
import openstudio
import ifcopenshell
from . import ifc_topologic

class SvEnergyModelByImportedIFC(bpy.types.Node, SverchCustomTreeNode):
  """
  Triggers: Energy model by IFC
  Tooltip: Creates an Energy Model from the input IFC
  """
  bl_idname = 'SvEnergyModelByImportedIFC'
  bl_label = 'EnergyModel.ByImportedIFC'

  def sv_init(self, context):
    self.inputs.new('SvStringsSocket', 'IFC')
    self.inputs.new('SvStringsSocket', 'Weather file path')
    self.inputs.new('SvStringsSocket', 'Design day file path')
    self.inputs.new('SvStringsSocket', 'Default space type')
    self.inputs.new('SvStringsSocket', 'Default construction set')
    self.inputs.new('SvStringsSocket', 'Heating temperature')
    self.inputs.new('SvStringsSocket', 'Cooling temperature')

    self.outputs.new('SvStringsSocket', 'Energy model')

  def process(self):
    if not any(socket.is_linked for socket in self.outputs):
      return

    ifc_files = self.inputs['IFC'].sv_get(deepcopy=False)[0]
    epw_paths = self.inputs['Weather file path'].sv_get(deepcopy=False)[0]
    ddy_paths = self.inputs['Design day file path'].sv_get(deepcopy=False)[0]
    space_types = self.inputs['Default space type'].sv_get(deepcopy=False)[0]
    construction_sets = self.inputs['Default construction set'].sv_get(deepcopy=False)[0]
    htg_temps = self.inputs['Heating temperature'].sv_get(deepcopy=False)[0]
    clg_temps = self.inputs['Cooling temperature'].sv_get(deepcopy=False)[0]

    os_models = []
    for idx, ifc_file in enumerate(ifc_files):
      epw_path = epw_paths[idx]
      ddy_path = ddy_paths[idx]
      space_type = space_types[idx]
      construction_set = construction_sets[idx]
      htg_temp = htg_temps[idx]
      clg_temp = clg_temps[idx]

      os_model = openstudio.model.Model()
      epw_file = openstudio.openstudioutilitiesfiletypes.EpwFile.load(openstudio.toPath(epw_path))
      if epw_file.is_initialized():
        epw_file = epw_file.get()
        openstudio.model.WeatherFile.setWeatherFile(os_model, epw_file)
      ddy_model = openstudio.openstudioenergyplus.loadAndTranslateIdf(openstudio.toPath(ddy_path))
      if ddy_model.is_initialized():
        ddy_model = ddy_model.get()
        for ddy in ddy_model.getObjectsByType(openstudio.IddObjectType("OS:SizingPeriod:DesignDay")):
          os_model.addObject(ddy.clone())
      os_model.getBuilding().setSpaceType(space_type.clone(os_model).to_SpaceType().get())
      os_model.getBuilding().setDefaultConstructionSet(construction_set.clone(os_model).to_DefaultConstructionSet().get())

      htg_sch = openstudio.model.ScheduleConstant(os_model)
      htg_sch.setValue(htg_temp)
      clg_sch = openstudio.model.ScheduleConstant(os_model)
      clg_sch.setValue(clg_temp)
      thermostat = openstudio.model.ThermostatSetpointDualSetpoint(os_model)
      thermostat.setHeatingSetpointTemperatureSchedule(htg_sch)
      thermostat.setCoolingSetpointTemperatureSchedule(clg_sch)

      ifc2os = {}
      for ifc_material_layer in ifc_file.by_type('IfcMaterialLayer'):
        if not ifc_material_layer.ToMaterialLayerSet:
          continue

        os_standard_opaque_material = openstudio.model.StandardOpaqueMaterial(os_model)
        os_standard_opaque_material.setName(ifc_material_layer.Material.Name + " - " + str(ifc_material_layer.LayerThickness))
        os_standard_opaque_material.setThickness(float(ifc_material_layer.LayerThickness))
        ifc2os[ifc_material_layer] = os_standard_opaque_material

      for ifc_material_layer_set in ifc_file.by_type('IfcMaterialLayerSet'):
        os_construction = openstudio.model.Construction(os_model)
        if ifc_material_layer_set.LayerSetName is not None:
          os_construction.setName(ifc_material_layer_set.LayerSetName)
        os_construction.setLayers([ ifc2os[ifc_material_layer] for ifc_material_layer in ifc_material_layer_set.MaterialLayers ])
        ifc2os[ifc_material_layer_set] = os_construction

      for ifc_building_storey in ifc_file.by_type('IfcBuildingStorey'):
        if not ifc_building_storey.IsDecomposedBy:
          continue

        ifc_spaces = [x for x in ifc_building_storey.IsDecomposedBy[0].RelatedObjects if x.is_a("IfcSpace")]
        if not ifc_spaces:
          continue

        os_building_story = openstudio.model.BuildingStory(os_model)
        os_building_story.setName(ifc_building_storey.Name)
        if ifc_building_storey.Elevation:
          os_building_story.setNominalZCoordinate(float(ifc_building_storey.Elevation))
        for ifc_space in ifc_spaces:
          if ifc_space.PredefinedType == "EXTERNAL":
            continue

          os_space = openstudio.model.Space(os_model)
          os_space.setName(ifc_space.Name)
          os_space.setBuildingStory(os_building_story)
          space_matrix = ifcopenshell.util.placement.get_local_placement(ifc_space.ObjectPlacement)
          os_space.setXOrigin(space_matrix[0,-1])
          os_space.setYOrigin(space_matrix[1,-1])
          os_space.setZOrigin(space_matrix[2,-1])

          for ifc_rel_space_boundary in ifc_space.BoundedBy:
            if ifc_rel_space_boundary.ParentBoundary is not None:
              continue

            vertices = ifc_topologic.getLocalVertices(ifc_rel_space_boundary, 0.0)
            os_surface = openstudio.model.Surface([ openstudio.Point3d(v[0], v[1], v[2]) for v in vertices ], os_model)
            if ifc_rel_space_boundary.Name is not None:
              os_surface.setName(ifc_rel_space_boundary.Name)
            os_surface.setSpace(os_space)
            if ifc_rel_space_boundary.CorrespondingBoundary is None:
              if ifc_rel_space_boundary.Description == "2a":
                os_surface.setOutsideBoundaryCondition("Outdoors")
              elif ifc_rel_space_boundary.Description == "2b":
                os_surface.setOutsideBoundaryCondition("Adiabatic")
            else:
              if ifc_rel_space_boundary.CorrespondingBoundary in ifc2os:
                os_surface.setAdjacentSurface(ifc2os[ifc_rel_space_boundary.CorrespondingBoundary])
              else:
                os_surface.setOutsideBoundaryCondition("Outdoors")
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

                os_surface.setConstruction(ifc2os[ifc_material])
                break
            ifc2os[ifc_rel_space_boundary] = os_surface

            for ifc_inner_boundary in ifc_rel_space_boundary.InnerBoundaries:
              if ifc_inner_boundary.ParentBoundary != ifc_rel_space_boundary:
                continue

              vertices = ifc_topologic.getLocalVertices(ifc_inner_boundary, 0.0)
              os_sub_surface = openstudio.model.SubSurface([ openstudio.Point3d(v[0], v[1], v[2]) for v in vertices ], os_model)
              if ifc_inner_boundary.Name is not None:
                os_sub_surface.setName(ifc_inner_boundary.Name)
              if ifc_inner_boundary.RelatedBuildingElement.is_a("IfcDoor"):
                os_sub_surface.setSubSurfaceType("Door")
              elif ifc_inner_boundary.RelatedBuildingElement.is_a("IfcWindow"):
                os_sub_surface.setSubSurfaceType("FixedWindow")
              os_sub_surface.setSurface(os_surface)
              if (ifc_inner_boundary.CorrespondingBoundary is not None and
                ifc_inner_boundary.CorrespondingBoundary in ifc2os):
                os_sub_surface.setAdjacentSubSurface(ifc2os[ifc_inner_boundary.CorrespondingBoundary])
              ifc2os[ifc_inner_boundary] = os_sub_surface

          thermal_zone = openstudio.model.ThermalZone(os_model)
          thermal_zone.setName("Thermal zone: " + os_space.name().get())
          thermal_zone.setUseIdealAirLoads(True)
          thermal_zone.setThermostatSetpointDualSetpoint(thermostat)
          os_space.setThermalZone(thermal_zone)
      os_models.append(os_model)

    self.outputs['Energy model'].sv_set([os_models])

def register():
  bpy.utils.register_class(SvEnergyModelByImportedIFC)

def unregister():
  bpy.utils.unregister_class(SvEnergyModelByImportedIFC)
