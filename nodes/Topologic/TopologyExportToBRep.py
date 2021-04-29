import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(topologyList, filepath, overwrite):
	# Make sure the file extension is .BREP
	ext = filepath[len(filepath)-5:len(filepath)]
	if ext.lower() != ".brep":
		filepath = filepath+".brep"
	f = None
	try:
		if overwrite == True:
			f = open(filepath, "w")
		else:
			f = open(filepath, "x") # Try to create a new File
	except:
		raise Exception("Error: Could not create a new file at the following location: "+filepath)
	if (f):
		if len(topologyList) > 1:
			stl_top = cppyy.gbl.std.list[topologic.Topology.Ptr]()
			for aTopology in topologyList:
				stl_top.push_back(aTopology)
			cluster = topologic.Cluster.ByTopologies(stl_top)
			topString = str(cluster.String())
		else:
			topString = str(topologyList[0].String())
		f.write(topString)
		f.close()	
		return True
	return False

		
class SvTopologyExportToBRep(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Exports the input Topology to a BREP file   
	"""
	bl_idname = 'SvTopologyExportToBRep'
	bl_label = 'Topology.ExportToBRep'
	OverwriteProp: BoolProperty(name="Overwrite", default=True, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.inputs.new('SvStringsSocket', 'File Path')
		self.inputs.new('SvStringsSocket', 'Overwrite File').prop_name = 'OverwriteProp'
		self.outputs.new('SvStringsSocket', 'Status')

	def process(self):
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Status'].sv_set([False])
			return
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)
		topologyList = flatten(topologyList)
		filepath = self.inputs['File Path'].sv_get(deepcopy=False)[0][0] #accept only one file path 
		overwrite = self.inputs['Overwrite File'].sv_get(deepcopy=False)[0][0] #accept only one overwrite flag
		self.outputs['Status'].sv_set([processItem(topologyList, filepath, overwrite)])

def register():
	bpy.utils.register_class(SvTopologyExportToBRep)

def unregister():
	bpy.utils.unregister_class(SvTopologyExportToBRep)
