# * This file is part of Topologic software library.
# * Copyright(C) 2021, Cardiff University and University College London
# * 
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU Affero General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# * 
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU Affero General Public License for more details.
# * 
# * You should have received a copy of the GNU Affero General Public License
# * along with this program. If not, see <https://www.gnu.org/licenses/>.


bl_info = {
	"name": "Topologic",
	"author": "Wassim Jabi",
	"version": "0.8.3.0",
	"blender": (3, 2, 0),
	"location": "Node Editor",
	"category": "Node",
	"description": "Topologic enables logical, hierarchical and topological modelling.",
	"warning": "",
	"wiki_url": "http://topologic.app",
    "support": "COMMUNITY",
	"tracker_url": "https://github.com/wassimj/TopologicSverchok/issues"
}

import sys
import os, re
from sys import platform
import bpy
blenderVersion =  "Blender"+str(bpy.app.version[0])+str(bpy.app.version[1])

sitePackagesFolderName = os.path.join(os.path.dirname(os.path.realpath(__file__)), "site-packages")
topologicFolderName = [filename for filename in os.listdir(sitePackagesFolderName) if filename.startswith("topologic")][0]
topologicPath = os.path.join(sitePackagesFolderName, topologicFolderName)
sys.path.append(topologicPath)
topologicPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "site-packages")
sys.path.append(topologicPath)

import importlib
from sverchok.ui.nodeview_space_menu import add_node_menu

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

__version__ = '0.8.2.3'
__version_info__ = tuple([ int(num) for num in __version__.split('.')])

#from topologicsverchok import icons
# make sverchok the root module name, (if sverchok dir not named exactly "sverchok")

if __name__ != "topologicsverchok":
	sys.modules["topologicsverchok"] = sys.modules[__name__]

def nodes_index():
	coreNodes = [
                ("Topologic.Version", "SvTopologicVersion"),
                ("Topologic.OpenFilePath", "SvTopologicOpenFilePath"),
                ("Topologic.VertexByCoordinates", "SvVertexByCoordinates"),
                ("Topologic.VertexByObjectLocation", "SvVertexByObjectLocation"),
                ("Topologic.VertexCoordinates", "SvVertexCoordinates"),
                ("Topologic.VertexDistance", "SvVertexDistance"),
                ("Topologic.VertexEnclosingCell", "SvVertexEnclosingCell"),
                ("Topologic.VertexNearestTopology", "SvVertexNearestTopology"),
                ("Topologic.VertexNearestVertex", "SvVertexNearestVertex"),
                ("Topologic.VertexProject", "SvVertexProject"),
                ("Topologic.EdgeByStartVertexEndVertex", "SvEdgeByStartVertexEndVertex"),
                ("Topologic.EdgeByVertices", "SvEdgeByVertices"),
                ("Topologic.EdgeDirection", "SvEdgeDirection"),
                ("Topologic.EdgeStartVertex", "SvEdgeStartVertex"),
                ("Topologic.EdgeEndVertex", "SvEdgeEndVertex"),
                ("Topologic.EdgeLength", "SvEdgeLength"),
                ("Topologic.EdgeParameterAtVertex", "SvEdgeParameterAtVertex"),
                ("Topologic.EdgeVertexByDistance", "SvEdgeVertexByDistance"),
                ("Topologic.EdgeVertexByParameter", "SvEdgeVertexByParameter"),
                ("Topologic.WireByEdges", "SvWireByEdges"),
                ("Topologic.WireByVertices", "SvWireByVertices"),
                ("Topologic.WireCircle", "SvWireCircle"),
                ("Topologic.WireCycles", "SvWireCycles"),
                ("Topologic.WireEllipse", "SvWireEllipse"),
                ("Topologic.WireIsClosed", "SvWireIsClosed"),
                ("Topologic.WireIsovist", "SvWireIsovist"),
                ("Topologic.WireIsSimilar", "SvWireIsSimilar"),
                ("Topologic.WireLength", "SvWireLength"),
                ("Topologic.WireProject", "SvWireProject"),
                ("Topologic.WireRectangle", "SvWireRectangle"),
                ("Topologic.WireRemoveCollinearEdges", "SvWireRemoveCollinearEdges"),
                ("Topologic.WireSplit", "SvWireSplit"),
                ("Topologic.WireStar", "SvWireStar"),
                ("Topologic.WireTrapezoid", "SvWireTrapezoid"),
                ("Topologic.FaceAddInternalBoundaries", "SvFaceAddInternalBoundaries"),
                ("Topologic.FaceArea", "SvFaceArea"),
                ("Topologic.FaceBoundingFace", "SvFaceBoundingFace"),
                ("Topologic.FaceByEdges", "SvFaceByEdges"),
                ("Topologic.FaceByShell", "SvFaceByShell"),
                ("Topologic.FaceByWire", "SvFaceByWire"),
                ("Topologic.FaceByWires", "SvFaceByWires"),
                ("Topologic.FaceByVertices", "SvFaceByVertices"),
                ("Topologic.FaceCompactness", "SvFaceCompactness"),
                ("Topologic.FaceExternalBoundary", "SvFaceExternalBoundary"),
                ("Topologic.FaceFacingToward", "SvFaceFacingToward"),
                ("Topologic.FaceFlatten", "SvFaceFlatten"),
                ("Topologic.FaceGridByDistances", "SvFaceGridByDistances"),
                ("Topologic.FaceGridByParameters", "SvFaceGridByParameters"),
                ("Topologic.FaceInternalVertex", "SvFaceInternalVertex"),
                ("Topologic.FaceIsInside", "SvFaceIsInside"),
                ("Topologic.FaceInternalBoundaries", "SvFaceInternalBoundaries"),
                ("Topologic.FaceNormalAtParameters", "SvFaceNormalAtParameters"),
                ("Topologic.FaceTrimByWire", "SvFaceTrimByWire"),
                ("Topologic.FaceVertexByParameters", "SvFaceVertexByParameters"),
                ("Topologic.FaceVertexParameters", "SvFaceVertexParameters"),
                ("Topologic.ApertureByTopologyContext", "SvApertureByTopologyContext"),
                ("Topologic.ApertureTopology", "SvApertureTopology"),
                ("Topologic.ShellByFaces", "SvShellByFaces"),
                ("Topologic.ShellByLoft", "SvShellByLoft"),
                ("Topologic.ShellExternalBoundary", "SvShellExternalBoundary"),
                ("Topologic.ShellHyperbolicParaboloid", "SvShellHyperbolicParaboloid"),
                ("Topologic.ShellInternalBoundaries", "SvShellInternalBoundaries"),
                ("Topologic.ShellIsClosed", "SvShellIsClosed"),
                ("Topologic.ShellPie", "SvShellPie"),
                ("Topologic.ShellTessellatedDisk", "SvShellTessellatedDisk"),
                ("Topologic.CellCone", "SvCellCone"),
                ("Topologic.CellCylinder", "SvCellCylinder"),
                ("Topologic.CellByFaces", "SvCellByFaces"),
                ("Topologic.CellByLoft", "SvCellByLoft"),
                ("Topologic.CellByShell", "SvCellByShell"),
                ("Topologic.CellByThickenedFace", "SvCellByThickenedFace"),
                ("Topologic.CellCompactness", "SvCellCompactness"),
                ("Topologic.CellExternalBoundary", "SvCellExternalBoundary"),
                ("Topologic.CellHyperboloid", "SvCellHyperboloid"),
                ("Topologic.CellInternalBoundaries", "SvCellInternalBoundaries"),
                ("Topologic.CellInternalVertex", "SvCellInternalVertex"),
                ("Topologic.CellIsInside", "SvCellIsInside"),
                ("Topologic.CellPipe", "SvCellPipe"),
                ("Topologic.CellPrism", "SvCellPrism"),
                ("Topologic.CellSets", "SvCellSets"),
                ("Topologic.CellSphere", "SvCellSphere"),
                ("Topologic.CellSuperCells", "SvCellSuperCells"),
                ("Topologic.CellSurfaceArea", "SvCellSurfaceArea"),
                ("Topologic.CellTorus", "SvCellTorus"),
                ("Topologic.CellVolume", "SvCellVolume"),
                ("Topologic.CellComplexByFaces", "SvCellComplexByFaces"),
                ("Topologic.CellComplexByCells", "SvCellComplexByCells"),
                ("Topologic.CellComplexByLoft", "SvCellComplexByLoft"),
                ("Topologic.CellComplexDecompose", "SvCellComplexDecompose"),
                ("Topologic.CellComplexExternalBoundary", "SvCellComplexExternalBoundary"),
                ("Topologic.CellComplexInternalBoundaries", "SvCellComplexInternalBoundaries"),
                ("Topologic.CellComplexNonManifoldFaces", "SvCellComplexNonManifoldFaces"),
                ("Topologic.CellComplexPrism", "SvCellComplexPrism"),
                ("Topologic.ClusterByTopologies", "SvClusterByTopologies"),
                ("Topologic.ContextByTopologyParameters", "SvContextByTopologyParameters"),
                ("Topologic.ContextTopology", "SvContextTopology"),
                ("Topologic.TopologyAddApertures", "SvTopologyAddApertures"),
                ("Topologic.TopologyAddContent", "SvTopologyAddContent"),
                ("Topologic.TopologyAddDictionary", "SvTopologyAddDictionary"),
                ("Topologic.TopologyAdjacentTopologies", "SvTopologyAdjacentTopologies"),
                ("Topologic.TopologyAnalyze", "SvTopologyAnalyze"),
                ("Topologic.TopologyApertures", "SvTopologyApertures"),
                ("Topologic.TopologyBlenderGeometry", "SvTopologyBlenderGeometry"),
                ("Topologic.TopologyBoolean", "SvTopologyBoolean"),
                ("Topologic.TopologyByGeometry", "SvTopologyByGeometry"),
                ("Topologic.TopologyByImportedBRep", "SvTopologyByImportedBRep"),
                ("Topologic.TopologyByImportedJSONMK1", "SvTopologyByImportedJSONMK1"),
                ("Topologic.TopologyByImportedJSONMK2", "SvTopologyByImportedJSONMK2"),
                ("Topologic.TopologyByOCCTShape", "SvTopologyByOCCTShape"),
                ("Topologic.TopologyByString", "SvTopologyByString"),
                ("Topologic.TopologyCenterOfMass", "SvTopologyCenterOfMass"),
                ("Topologic.TopologyCentroid", "SvTopologyCentroid"),
                ("Topologic.TopologyContent", "SvTopologyContent"),
                ("Topologic.TopologyContext", "SvTopologyContext"),
                ("Topologic.TopologyCopy", "SvTopologyCopy"),
                ("Topologic.TopologyDecodeInformation", "SvTopologyDecodeInformation"),
                ("Topologic.TopologyDictionary", "SvTopologyDictionary"),
                ("Topologic.TopologyDimensionality", "SvTopologyDimensionality"),
                ("Topologic.TopologyDivide", "SvTopologyDivide"),
                ("Topologic.TopologyEncodeInformation", "SvTopologyEncodeInformation"),
                ("Topologic.TopologyExplode", "SvTopologyExplode"),
                ("Topologic.TopologyExportToBRep", "SvTopologyExportToBRep"),
                ("Topologic.TopologyExportToJSONMK1", "SvTopologyExportToJSONMK1"),
                ("Topologic.TopologyExportToJSONMK2", "SvTopologyExportToJSONMK2"),
                ("Topologic.TopologyFilter", "SvTopologyFilter"),
                ("Topologic.TopologyGeometry", "SvTopologyGeometry"),
                ("Topologic.TopologyIsPlanar", "SvTopologyIsPlanar"),
                ("Topologic.TopologyIsSame", "SvTopologyIsSame"),
                ("Topologic.TopologyMergeAll", "SvTopologyMergeAll"),
                ("Topologic.TopologyOCCTShape", "SvTopologyOCCTShape"),
                ("Topologic.TopologyPlace", "SvTopologyPlace"),
                ("Topologic.TopologyRemoveCollinearEdges", "SvTopologyRemoveCollinearEdges"),
                ("Topologic.TopologyRemoveContent", "SvTopologyRemoveContent"),
                ("Topologic.TopologyRotate", "SvTopologyRotate"),
                ("Topologic.TopologyScale", "SvTopologyScale"),
                ("Topologic.TopologySelectSubTopology", "SvTopologySelectSubTopology"),
                ("Topologic.TopologySelfMerge", "SvTopologySelfMerge"),
                ("Topologic.TopologySetDictionary", "SvTopologySetDictionary"),
                ("Topologic.TopologySharedTopologies", "SvTopologySharedTopologies"),
                ("Topologic.TopologySortBySelectors", "SvTopologySortBySelectors"),
                ("Topologic.TopologySpin", "SvTopologySpin"),
                ("Topologic.TopologyString", "SvTopologyString"),
                ("Topologic.TopologySubTopologies", "SvTopologySubTopologies"),
                ("Topologic.TopologySuperTopologies", "SvTopologySuperTopologies"),
                ("Topologic.TopologyTransferDictionaries", "SvTopologyTransferDictionaries"),
                ("Topologic.TopologyTransferDictionariesBySelectors", "SvTopologyTransferDictionariesBySelectors"),
                ("Topologic.TopologyTransform", "SvTopologyTransform"),
                ("Topologic.TopologyTranslate", "SvTopologyTranslate"),
                ("Topologic.TopologyTriangulate", "SvTopologyTriangulate"),
                ("Topologic.TopologyType", "SvTopologyType"),
                ("Topologic.TopologyTypeID", "SvTopologyTypeID"),
                ("Topologic.DictionaryByKeysValues", "SvDictionaryByKeysValues"),
                ("Topologic.DictionaryByMergedDictionaries", "SvDictionaryByMergedDictionaries"),
                ("Topologic.DictionaryByObjectProperties", "SvDictionaryByObjectProperties"),
                ("Topologic.DictionarySetValueAtKey", "SvDictionarySetValueAtKey"),
                ("Topologic.DictionaryValueAtKey", "SvDictionaryValueAtKey"),
                ("Topologic.DictionaryKeys", "SvDictionaryKeys"),
                ("Topologic.DictionaryValues", "SvDictionaryValues"),
                ("Topologic.GraphAddEdge", "SvGraphAddEdge"),
                ("Topologic.GraphAddVertex", "SvGraphAddVertex"),
                ("Topologic.GraphAdjacentVertices", "SvGraphAdjacentVertices"),
                ("Topologic.GraphAllPaths", "SvGraphAllPaths"),
                ("Topologic.GraphByImportedDGCNN", "SvGraphByImportedDGCNN"),
                ("Topologic.GraphByTopology", "SvGraphByTopology"),
                ("Topologic.GraphByVerticesEdges", "SvGraphByVerticesEdges"),
                ("Topologic.GraphConnect", "SvGraphConnect"),
                ("Topologic.GraphContainsEdge", "SvGraphContainsEdge"),
                ("Topologic.GraphContainsVertex", "SvGraphContainsVertex"),
                ("Topologic.GraphDegreeSequence", "SvGraphDegreeSequence"),
                ("Topologic.GraphDensity", "SvGraphDensity"),
                ("Topologic.GraphDepthMap", "SvGraphDepthMap"),
                ("Topologic.GraphDiameter", "SvGraphDiameter"),
                ("Topologic.GraphEdge", "SvGraphEdge"),
                ("Topologic.GraphEdges", "SvGraphEdges"),
                ("Topologic.GraphExportToDGCNN", "SvGraphExportToDGCNN"),
                ("Topologic.GraphIsComplete", "SvGraphIsComplete"),
                ("Topologic.GraphIsErdoesGallai", "SvGraphIsErdoesGallai"),
                ("Topologic.GraphIsolatedVertices", "SvGraphIsolatedVertices"),
                ("Topologic.GraphMaximumDelta", "SvGraphMaximumDelta"),
                ("Topologic.GraphMinimumDelta", "SvGraphMinimumDelta"),
                ("Topologic.GraphMST", "SvGraphMST"),
                ("Topologic.GraphNearestVertex", "SvGraphNearestVertex"),
                ("Topologic.GraphPath", "SvGraphPath"),
                ("Topologic.GraphRemoveEdge", "SvGraphRemoveEdge"),
                ("Topologic.GraphRemoveVertex", "SvGraphRemoveVertex"),
                ("Topologic.GraphShortestPath", "SvGraphShortestPath"),
                ("Topologic.GraphShortestPaths", "SvGraphShortestPaths"),
                ("Topologic.GraphTopologicalDistance", "SvGraphTopologicalDistance"),
                ("Topologic.GraphTopology", "SvGraphTopology"),
                ("Topologic.GraphTree", "SvGraphTree"),
                ("Topologic.GraphVertexDegree", "SvGraphVertexDegree"),
                ("Topologic.GraphVertices", "SvGraphVertices"),
                ("Topologic.GraphVerticesAtKeyValue", "SvGraphVerticesAtKeyValue"),
                ("Topologic.ColorByObjectColor", "SvColorByObjectColor"),
                ("Topologic.ColorByValueInRange", "SvColorByValueInRange"),
                ("Topologic.MatrixByRotation", "SvMatrixByRotation"),
                ("Topologic.MatrixByScaling", "SvMatrixByScaling"),
                ("Topologic.MatrixByTranslation", "SvMatrixByTranslation"),
                ("Topologic.MatrixMultiply", "SvMatrixMultiply"),
                ("Topologic.Run", "SvTopologicRun"),
                ("Topologic.InstallDependencies", "SvTopologicInstallDependencies")]

	visgraphNodes = [("Topologic.GraphVisibilityGraph", "SvGraphVisibilityGraph")]
	numpyNodes = [("Topologic.TopologyRemoveCoplanarFaces", "SvTopologyRemoveCoplanarFaces"),
                  ("Topologic.FaceByOffset", "SvFaceByOffset"),
                  ("Topologic.EdgeAngle", "SvEdgeAngle"),
                  ("Topologic.EdgeIsCollinear", "SvEdgeIsCollinear"),
                  ("Topologic.FaceAngle", "SvFaceAngle"),
                  ("Topologic.FaceIsCoplanar", "SvFaceIsCoplanar"),
                  ("Topologic.TopologyClusterFaces", "SvTopologyClusterFaces")]
	ifcNodes = [("Topologic.IFCAdd2ndLevelBoundaries", "SvIFCAdd2ndLevelBoundaries"),
                ("Topologic.IFCBuildingElements", "SvIFCBuildingElements"),
                ("Topologic.IFCClashDetection", "SvIFCClashDetection"),
                ("Topologic.IFCConnectBuildingElements", "SvIFCConnectBuildingElements"),
                ("Topologic.IFCCreateSpaces", "SvIFCCreateSpaces"),
                ("Topologic.IFCReadFile", "SvIFCReadFile"),
                ("Topologic.IFCWriteFile", "SvIFCWriteFile"),
                ("Topologic.TopologyByImportedIFC", "SvTopologyByImportedIFC")]
	web3Nodes = [("Topologic.ContractByParameters", "SvContractByParameters")]
	ipfsNodes = [("Topologic.TopologyByImportedIPFS", "SvTopologyByImportedIPFS"),
                 ("Topologic.TopologyExportToIPFS", "SvTopologyExportToIPFS")]
	openstudioNodes = [("Topologic.EnergyModelByImportedOSM", "SvEnergyModelByImportedOSM"),
                ("Topologic.EnergyModelByTopology", "SvEnergyModelByTopology"),
                ("Topologic.EnergyModelColumnNames", "SvEnergyModelColumnNames"),
                ("Topologic.EnergyModelDefaultConstructionSets", "SvEnergyModelDefaultConstructionSets"),
                ("Topologic.EnergyModelDefaultScheduleSets", "SvEnergyModelDefaultScheduleSets"),
                ("Topologic.EnergyModelExportToGbXML", "SvEnergyModelExportToGbXML"),
                ("Topologic.EnergyModelExportToHBJSON", "SvEnergyModelExportToHBJSON"),
                ("Topologic.EnergyModelExportToIDF", "SvEnergyModelExportToIDF"),
                ("Topologic.EnergyModelExportToOSM", "SvEnergyModelExportToOSM"),
                ("Topologic.EnergyModelGbXMLString", "SvEnergyModelGbXMLString"),
                ("Topologic.EnergyModelQuery", "SvEnergyModelQuery"),
                ("Topologic.EnergyModelReportNames", "SvEnergyModelReportNames"),
                ("Topologic.EnergyModelRowNames", "SvEnergyModelRowNames"),
                ("Topologic.EnergyModelRunSimulation", "SvEnergyModelRunSimulation"),
                ("Topologic.EnergyModelSpaceTypes", "SvEnergyModelSpaceTypes"),
                ("Topologic.EnergyModelSqlFile", "SvEnergyModelSqlFile"),
                ("Topologic.EnergyModelTableNames", "SvEnergyModelTableNames"),
                ("Topologic.EnergyModelTopologies", "SvEnergyModelTopologies"),
                ("Topologic.EnergyModelUnits", "SvEnergyModelUnits")]
	honeybeeNodes = [("Topologic.HBModelByTopology", "SvHBModelByTopology"),
                ("Topologic.HBModelExportToHBJSON", "SvHBModelExportToHBJSON"),
                ("Topologic.HBModelString", "SvHBModelString"),
                ("Topologic.HBConstructionSetByIdentifier", "SvHBConstructionSetByIdentifier"),
                ("Topologic.HBConstructionSets", "SvHBConstructionSets"),
                ("Topologic.HBProgramTypeByIdentifier", "SvHBProgramTypeByIdentifier"),
                ("Topologic.HBProgramTypes", "SvHBProgramTypes")]
	neo4jNodes = [("Topologic.GraphByNeo4jGraph", "SvGraphByNeo4jGraph"),
                ("Topologic.Neo4jGraphByParameters", "SvNeo4jGraphByParameters"),
                ("Topologic.Neo4jGraphDeleteAll", "SvNeo4jGraphDeleteAll"),
                ("Topologic.Neo4jGraphNodeLabels", "SvNeo4jGraphNodeLabels"),
                ("Topologic.Neo4jGraphSetGraph", "SvNeo4jGraphSetGraph")]
	speckleNodes = [("Topologic.SpeckleBranchByID", "SvSpeckleBranchByID"),
                ("Topologic.SpeckleBranchesByStream", "SvSpeckleBranchesByStream"),
                ("Topologic.SpeckleClientByHost", "SvSpeckleClientByHost"),
                ("Topologic.SpeckleClientByURL", "SvSpeckleClientByURL"),
                ("Topologic.SpeckleCommitByID", "SvSpeckleCommitByID"),
                ("Topologic.SpeckleCommitByURL", "SvSpeckleCommitByURL"),
                ("Topologic.SpeckleCommitDelete", "SvSpeckleCommitDelete"),
                ("Topologic.SpeckleCommitsByBranch", "SvSpeckleCommitsByBranch"),
                ("Topologic.SpeckleGlobalsByStream", "SvSpeckleGlobalsByStream"),
                ("Topologic.SpeckleObjects", "SvSpeckleObjects"),
                ("Topologic.SpeckleReceive", "SvSpeckleReceive"),
                ("Topologic.SpeckleSend", "SvSpeckleSend"),
                ("Topologic.SpeckleSendObject", "SvSpeckleSendObject"),
                ("Topologic.SpeckleStreamByID", "SvSpeckleStreamByID"),
                ("Topologic.SpeckleStreamByURL", "SvSpeckleStreamByURL"),
                ("Topologic.SpeckleStreamsByClient", "SvSpeckleStreamsByClient")]
	dglNodes = [("Topologic.DGLAccuracy", "SvDGLAccuracy"),
                ("Topologic.DGLClassifierByFilePath", "SvDGLClassifierByFilePath"),
                ("Topologic.DGLDatasetByDGLGraphs", "SvDGLDatasetByDGLGraphs"),
                ("Topologic.DGLDatasetByImportedCSV_NC", "SvDGLDatasetByImportedCSV_NC"),
                ("Topologic.DGLDatasetBySamples", "SvDGLDatasetBySamples"),
                ("Topologic.DGLDatasetBySamples_NC", "SvDGLDatasetBySamples_NC"),
                ("Topologic.DGLDatasetGraphs_NC", "SvDGLDatasetGraphs_NC"),
                ("Topologic.DGLGraphByGraph", "SvDGLGraphByGraph"),
                ("Topologic.DGLGraphByImportedCSV", "SvDGLGraphByImportedCSV"),
                ("Topologic.DGLGraphByImportedDGCNN", "SvDGLGraphByImportedDGCNN"),
                ("Topologic.DGLGraphEdgeData_NC", "SvDGLGraphEdgeData_NC"),
                ("Topologic.DGLGraphNodeData_NC", "SvDGLGraphNodeData_NC"),
                ("Topologic.DGLHyperparameters", "SvDGLHyperparameters"),
                ("Topologic.DGLOptimizer", "SvDGLOptimizer"),
                ("Topologic.DGLPredict", "SvDGLPredict"),
                ("Topologic.DGLPredict_NC", "SvDGLPredict_NC"),
                ("Topologic.DGLTrainClassifier", "SvDGLTrainClassifier"),
                ("Topologic.DGLTrainClassifier_NC", "SvDGLTrainClassifier_NC"),
                ("Topologic.DictionaryByDGLData", "SvDictionaryByDGLData")]

	hullNodes = [("Topologic.TopologyConvexHull", "SvTopologyConvexHull")]
	homemakerNodes = [("Topologic.HMIFCByCellComplex", "SvHMIFCByCellComplex"),
                ("Topologic.HMBlenderBIMByIFC", "SvHMBlenderBIMByIFC")]
	pandasNodes = [("Topologic.GraphExportToCSV", "SvGraphExportToCSV"),
                ("Topologic.GraphExportToCSV_NC", "SvGraphExportToCSV_NC")]
	plotlyNodes = [("Topologic.DGLPlot", "SvDGLPlot")]
	ifchoneybeeNodes = [("Topologic.IFCExportToHBJSON", "SvIFCExportToHBJSON")]
	osifcNodes = [("Topologic.EnergyModelByImportedIFC", "SvEnergyModelByImportedIFC")]
	osifc = 0
	pyobbNodes = [("Topologic.TopologyBoundingBox", "SvTopologyBoundingBox")]

	try:
		import numpy
		coreNodes = coreNodes+numpyNodes
	except:
		print("Topologic - Warning: Could not import numpy so some related nodes are not available.")
	try:
		import pyvisgraph
		coreNodes = coreNodes+visgraphNodes
	except:
		print("Topologic - Warning: Could not import pyvisgraph so some related nodes are not available.")
	try:
		import ifcopenshell
		import scipy
		coreNodes = coreNodes+ifcNodes
		osifc = osifc + 1
	except:
		print("Topologic - Warning: Could not import ifcopenshell and/or scipy so IFC nodes are not available.")
	try:
		import ipfshttpclient
		coreNodes = coreNodes+ipfsNodes
	except:
		print("Topologic - Warning: Could not import ipfshttpclient so IPFS nodes are not available.")
	try:
		import web3
		coreNodes = coreNodes+web3Nodes
	except:
		print("Topologic - Warning: Could not import web3 so Web3 nodes are not available.")
	try:
		import openstudio
		coreNodes = coreNodes+openstudioNodes
		osifc = osifc + 1
	except:
		print("Topologic - Warning: Could not import openstudio so OpenStudio nodes are not available.")
	try:
		import openstudio
		import honeybee
		from honeybee.model import Model
		import honeybee_energy
		import honeybee_radiance
		import ladybug
		import json
		coreNodes = coreNodes+honeybeeNodes
	except:
		print("Topologic - Warning: Could not import ladybug/honeybee/json so Honeybee nodes are not available.")
	try:
		import honeybee
		import honeybee_energy
		from honeybee.model import Model
		import ifcopenshell
		import numpy
		import scipy
		coreNodes = coreNodes+ifchoneybeeNodes
	except:
		print("Topologic - Warning: Could not import honeybee/ifcopenshell/numpy/scipy so IFCHoneybee nodes are not available.")
	try:
		import py2neo
		coreNodes = coreNodes+neo4jNodes
	except:
		print("Topologic - Warning: Could not import py2neo so Neo4j nodes are not available.")
	if osifc > 1:
		coreNodes = coreNodes+osifcNodes
	else:
		print("Topologic - Warning: Could not import either openstudio/ifcopenshell so some related nodes that require both to be installed are not available.")

	try:
		import specklepy
		import bpy_speckle
		coreNodes = coreNodes+speckleNodes
	except:
		print("Topologic - Warning: Could not import speckle so Speckle are not available.")

	try:
		import numpy
		import scipy
		import pandas
		import torch
		import networkx
		import tqdm
		import sklearn
		import dgl
		coreNodes = coreNodes+dglNodes
	except:
		print("Topologic - Warning: Could not import numpy/scipy/pandas/torch/networkx/dgl/tqdm/sklearn so DGL nodes are not available.")
	try:
		import plotly
		coreNodes = coreNodes+plotlyNodes
	except:
		print("Topologic - Warning: Could not import plotly so plot-related nodes are not available.")
	try:
		import numpy
		import scipy
		coreNodes = coreNodes+hullNodes
	except:
		print("Topologic - Warning: Could not import numpy/scipy so Convex Hull node is not available.")
	try:
		import ifcopenshell
		from blenderbim.bim import import_ifc
		from molior import Molior
		coreNodes = coreNodes+homemakerNodes
	except:
		print("Topologic - Warning: Could not import ifcopenshell/molior so Homemaker nodes are not available.")
	try:
		import pandas as pd
		coreNodes = coreNodes+pandasNodes
	except:
		print("Topologic - Warning: Could not import pandas so Topologic.GraphExportToCSV is not available.")
	try:
		import numpy
		import pyobb
		coreNodes = coreNodes+pyobbNodes
	except:
		print("Topologic - Warning: Could not import numpy and/or pyobb so some related nodes are not available.")
	return [("Topologic", coreNodes)]

def make_node_list():
	modules = []
	base_name = "topologicsverchok.nodes"
	index = nodes_index()
	for category, items in index:
		for module_name, node_name in items:
			module = importlib.import_module(f".{module_name}", base_name)
			modules.append(module)
	return modules

#imported_modules = [icons] + make_node_list()
imported_modules = make_node_list()

reload_event = False

def register_nodes():
	node_modules = make_node_list()
	for module in node_modules:
		module.register()
	#info("Registered %s nodes", len(node_modules))

def unregister_nodes():
	global imported_modules
	for module in reversed(imported_modules):
		module.unregister()


node_categories = [
    {"Topologic": [
        {"TP Vertex": [
            'SvVertexByCoordinates',
            'SvVertexByObjectLocation',
            'SvVertexCoordinates',
            'SvVertexDistance',
            'SvVertexEnclosingCell',
            'SvVertexNearestTopology',
            'SvVertexNearestVertex',
            'SvVertexProject',
        ]},
        {"TP Edge": [
            'SvEdgeAngle',
            'SvEdgeByStartVertexEndVertex',
            'SvEdgeByVertices',
            'SvEdgeDirection',
            'SvEdgeEndVertex',
            'SvEdgeIsCollinear',
            'SvEdgeLength',
            'SvEdgeParameterAtVertex',
            'SvEdgeStartVertex',
            'SvEdgeVertexByDistance',
            'SvEdgeVertexByParameter',
        ]},
        {"TP Wire": [
            'SvWireByEdges',
            'SvWireByVertices',
            'SvWireCircle',
            'SvWireCycles',
            'SvWireEllipse',
            'SvWireIsovist',
            'SvWireIsClosed',
            'SvWireIsSimilar',
            'SvWireLength',
            'SvWireProject',
            'SvWireRectangle',
            'SvRemoveCollinearEdges',
            'SvWireSplit',
            'SvWireStar',
            'SvWireTrapezoid',
        ]},
        {"TP Face": [
            'SvFaceAddInternalBoundaries',
            'SvFaceAngle',
            'SvFaceArea',
            'SvFaceBoundingFace',
            'SvFaceByEdges',
            'SvFaceByOffset',
            'SvFaceByShell',
            'SvFaceByVertices',
            'SvFaceByWire',
            'SvFaceByWires',
            'SvFaceCompactness',
            'SvFaceExternalBoundary',
            'SvFaceFacingToward',
            'SvFaceFlatten',
            'SvFaceGridByDistances',
            'SvFaceGridByParameters',
            'SvFaceInternalBoundaries',
            'SvFaceInternalVertex',
            'SvFaceIsCoplanar',
            'SvFaceIsInside',
            'SvFaceNormalAtParameters',
            'SvFaceTrimByWire',
            'SvFaceVertexByParameters',
            'SvFaceVertexParameters',
        ]},
        {"TP Shell": [
            'SvShellByFaces',
            'SvShellByLoft',
            'SvShellExternalBoundary',
            'SvShellHyperbolicParaboloid',
            'SvShellInternalBoundaries',
            'SvShellIsClosed',
            'SvShellPie',
            'SvShellTessellatedDisk',
        ]},
        {"TP Cell": [
            'SvCellByFaces',
            'SvCellCone',
            'SvCellCylinder',
            'SvCellByLoft',
            'SvCellByShell',
            'SvCellByThickenedFace',
            'SvCellCompactness',
            'SvCellExternalBoundary',
            'SvCellHyperboloid',
            'SvCellInternalBoundaries',
            'SvCellInternalVertex',
            'SvCellIsInside',
            'SvCellPipe',
            'SvCellPrism',
            'SvCellSets',
            'SvCellSphere',
            'SvCellSuperCells',
            'SvCellSurfaceArea',
            'SvCellTorus',
            'SvCellVolume',
        ]},
        {"TP CellComplex": [
            'SvCellComplexByCells',
            'SvCellComplexByFaces',
            'SvCellComplexByLoft',
            'SvCellComplexDecompose',
            'SvCellComplexExternalBoundary',
            'SvCellComplexInternalBoundaries',
            'SvCellComplexNonManifoldFaces',
            'SvCellComplexPrism',
        ]},
        {"TP Cluster": [
            'SvClusterByTopologies',
        ]},
        {"TP Topology": [
            'SvTopologyAddApertures',
            'SvTopologyAddContent',
            'SvTopologyAdjacentTopologies',
            'SvTopologyAnalyze',
            'SvTopologyApertures',
            'SvTopologyBlenderGeometry',
            'SvTopologyBoolean',
            'SvTopologyBoundingBox',
            'SvTopologyByGeometry',
            'SvTopologyByImportedBRep',
            'SvTopologyByImportedJSONMK1',
            'SvTopologyByImportedJSONMK2',
            'SvTopologyByOCCTShape',
            'SvTopologyByString',
            'SvTopologyCenterOfMass',
            'SvTopologyCentroid',
            'SvTopologyClusterFaces',
            'SvTopologyContent',
            'SvTopologyContext',
            'SvTopologyConvexHull',
            'SvTopologyCopy',
            'SvTopologyDecodeInformation',
            'SvTopologyDictionary',
            'SvTopologyDimensionality',
            'SvTopologyDivide',
            'SvTopologyEncodeInformation',
            'SvTopologyExplode',
            'SvTopologyExportToBRep',
            'SvTopologyExportToJSONMK1',
            'SvTopologyExportToJSONMK2',
            'SvTopologyFilter',
            'SvTopologyGeometry',
            'SvTopologyIsPlanar',
            'SvTopologyIsSame',
            'SvTopologyMergeAll',
            'SvTopologyOCCTShape',
            'SvTopologyPlace',
            'SvTopologyRotate',
            'SvTopologyRemoveCollinearEdges',
            'SvTopologyRemoveContent',
            'SvTopologyRemoveCoplanarFaces',
            'SvTopologyScale',
            'SvTopologySelectSubTopology',
            'SvTopologySelfMerge',
            'SvTopologySetDictionary',
            'SvTopologySharedTopologies',
            'SvTopologySortBySelectors',
            'SvTopologySpin',
            'SvTopologyString',
            'SvTopologySubTopologies',
            'SvTopologySuperTopologies',
            'SvTopologyTransferDictionaries',
            'SvTopologyTransferDictionariesBySelectors',
            'SvTopologyTransform',
            'SvTopologyTranslate',
            'SvTopologyTriangulate',
            'SvTopologyType',
            'SvTopologyTypeID',
            'SvTopologicRun',
        ]},
        {"TP Aperture": [
            'SvApertureByTopologyContext',
            'SvApertureTopology',
        ]},
        {"TP Color": [
            'SvColorByObjectColor',
            'SvColorByValueInRange',
        ]},
        {"TP Context": [
            'SvContextByTopologyParameters',
            'SvContextTopology',
        ]},
        {"TP Dictionary": [
            'SvDictionaryByDGLData',
            'SvDictionaryByKeysValues',
            'SvDictionaryByMergedDictionaries',
            'SvDictionaryByObjectProperties',
            'SvDictionarySetValueAtKey',
            'SvDictionaryValueAtKey',
            'SvDictionaryKeys',
            'SvDictionaryValues',
        ]},
        {"TP Graph": [
            'SvGraphAddEdge',
            'SvGraphAddVertex',
            'SvGraphAdjacentVertices',
            'SvGraphAllPaths',
            'SvGraphByImportedDGCNN',
            'SvGraphByTopology',
            'SvGraphByVerticesEdges',
            'SvGraphConnect',
            'SvGraphContainsEdge',
            'SvGraphContainsVertex',
            'SvGraphDegreeSequence',
            'SvGraphDensity',
            'SvGraphDepthMap',
            'SvGraphDiameter',
            'SvGraphEdge',
            'SvGraphEdges',
            'SvGraphExportToCSV',
            'SvGraphExportToCSV_NC',
            'SvGraphExportToDGCNN',
            'SvGraphIsComplete',
            'SvGraphIsErdoesGallai',
            'SvGraphIsolatedVertices',
            'SvGraphMaximumDelta',
            'SvGraphMinimumDelta',
            'SvGraphMST',
            'SvGraphNearestVertex',
            'SvGraphPath',
            'SvGraphRemoveEdge',
            'SvGraphRemoveVertex',
            'SvGraphShortestPath',
            'SvGraphShortestPaths',
            'SvGraphTopologicalDistance',
            'SvGraphTopology',
            'SvGraphTree',
            'SvGraphVertexDegree',
            'SvGraphVertices',
            'SvGraphVerticesAtKeyValue',
            'SvGraphVisibilityGraph',
        ]},
        {"TP Matrix": [
            'SvMatrixByRotation',
            'SvMatrixByScaling',
            'SvMatrixByTranslation',
            'SvMatrixMultiply',
        ]},
        {"TP Openstudio": [
            'SvEnergyModelByImportedIFC',
            'SvEnergyModelByImportedOSM',
            'SvEnergyModelByTopology',
            'SvHBJSONByTopology',
            'SvEnergyModelColumnNames',
            'SvEnergyModelDefaultConstructionSets',
            'SvEnergyModelDefaultScheduleSets',
            'SvEnergyModelExportToGbXML',
            'SvEnergyModelExportToHBJSON',
            'SvEnergyModelExportToOSM',
            'SvEnergyModelGbXMLString',
            'SvEnergyModelQuery',
            'SvEnergyModelReportNames',
            'SvEnergyModelRowNames',
            'SvEnergyModelRunSimulation',
            'SvEnergyModelSpaceTypes',
            'SvEnergyModelSqlFile',
            'SvEnergyModelTableNames',
            'SvEnergyModelTopologies',
            'SvEnergyModelUnits',
        ]},
        {"TP Honeybee": [
            'SvHBModelByTopology',
            'SvHBModelExportToHBJSON',
            'SvHBModelString',
            'SvHBConstructionSetByIdentifier',
            'SvHBConstructionSets',
            'SvHBProgramTypeByIdentifier',
            'SvHBProgramTypes',
        ]},
        {"TP IFC": [
            'SvIFCAdd2ndLevelBoundaries',
            'SvIFCBuildingElements',
            'SvEnergyModelByImportedIFC',
            'SvIFCClashDetection',
            'SvIFCConnectBuildingElements',
            'SvIFCCreateSpaces',
            'SvIFCExportToHBJSON',
            'SvIFCReadFile',
            'SvIFCWriteFile',
            'SvTopologyByImportedIFC',
        ]},
        {"TP Blockchain": [
            'SvContractByParameters',
            'SvTopologyByImportedIPFS',
            'SvTopologyExportToIPFS',
        ]},
        {"TP Neo4j": [
            'SvGraphByNeo4jGraph',
            'SvNeo4jGraphByParameters',
            'SvNeo4jGraphDeleteAll',
            'SvNeo4jGraphNodeLabels',
            'SvNeo4jGraphSetGraph',
        ]},
        {"TP Speckle": [
            'SvSpeckleBranchByID',
            'SvSpeckleBranchesByStream',
            'SvSpeckleClientByHost',
            'SvSpeckleClientByURL',
            'SvSpeckleCommitByID',
            'SvSpeckleCommitByURL',
            'SvSpeckleCommitDelete',
            'SvSpeckleCommitsByBranch',
            'SvSpeckleGlobalsByStream',
            'SvSpeckleObjects',
            'SvSpeckleReceive',
            'SvSpeckleSend',
            'SvSpeckleSendObject',
            'SvSpeckleStreamByID',
            'SvSpeckleStreamByURL',
            'SvSpeckleStreamsByClient',
        ]},
        {"TP DGL": [
            'SvDGLAccuracy',
            'SvDGLClassifierByFilePath',
            'SvDGLDatasetByDGLGraphs',
            'SvDGLDatasetByImportedCSV_NC',
            'SvDGLDatasetBySamples',
            'SvDGLDatasetBySamples_NC',
            'SvDGLDatasetGraphs_NC',
            'SvDGLGraphByGraph',
            'SvDGLGraphByImportedCSV',
            'SvDGLGraphByImportedDGCNN',
            'SvDGLGraphEdgeData_NC',
            'SvDGLGraphNodeData_NC',
            'SvDGLHyperparameters',
            'SvDGLOptimizer',
            'SvDGLPlot',
            'SvDGLPredict',
            'SvDGLPredict_NC',
            'SvDGLTrainClassifier',
            'SvDGLTrainClassifier_NC',
        ]},
        {"TP Homemaker": [
            'SvHMIFCByCellComplex',
            'SvHMBlenderBIMByIFC',
        ]},
        {"TP Utilities": [
            'SvTopologicInstallDependencies',
            'SvTopologicOpenFilePath',
            'SvTopologicVersion',
        ]},
    ]}
]

add_node_menu.append_from_config(node_categories)


def register():
    # settings.register()
    # icons.register()
    # sockets.register()
    register_nodes()
    add_node_menu.register()


def unregister():
    unregister_nodes()
    # sockets.unregister()
    # icons.unregister()
    # settings.unregister()
