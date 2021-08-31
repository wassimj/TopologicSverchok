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

import bpy
from bpy.props import StringProperty, FloatProperty
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

def processItem(item, tol):
	cell = None
	stl_faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	for aFace in item:
		stl_faces.push_back(aFace)
	cell = topologic.Cell.ByFaces(stl_faces, tol)
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	try:
		_ = cell.Vertices(vertices)
	except:
		raise Exception("Error: Could not create a valid Cell. Please check input.")
	if len(vertices) < 4:
		raise Exception("Error: Could not create a valid Cell. Please check input.")
	return cell

class SvCellByFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cell from the list of input Faces  
	"""
	bl_idname = 'SvCellByFaces'
	bl_label = 'Cell.ByFaces'
	Tol: FloatProperty(name='Tol', default=0.0001, min=0, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Faces')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		self.outputs['Cell'].sv_set([])
		if not any(socket.is_linked for socket in self.outputs):
			return
		faceList = self.inputs['Faces'].sv_get(deepcopy=True)
		tol = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)[0][0]

		if isinstance(faceList[0], list) == False:
			faceList = [faceList]
		outputs = []
		for faces in faceList:
			outputs.append(processItem(faces, tol))
		self.outputs['Cell'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvCellByFaces)

def unregister():
    bpy.utils.unregister_class(SvCellByFaces)
