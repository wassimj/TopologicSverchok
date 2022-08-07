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
from bpy.props import StringProperty, FloatProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def processItem(item, tol):
	cell = topologic.Cell.ByFaces(item, tol)
	if cell:
		return cell
	else:
		raise Exception("CellByFaces - Could not create a valid Cell")

class SvCellByFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cell from the list of input Faces  
	"""
	bl_idname = 'SvCellByFaces'
	bl_label = 'Cell.ByFaces'
	Tol: FloatProperty(name='Tol', default=0.0001, min=0, precision=4, update=updateNode)
	Level: IntProperty(name='Level', default =1,min=1, update = updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Faces')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.inputs.new('SvStringsSocket', 'Level').prop_name='Level'
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		self.outputs['Cell'].sv_set([])
		if not any(socket.is_linked for socket in self.outputs):
			return
		faceList = self.inputs['Faces'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)
		toleranceList = Replication.flatten(toleranceList)
		level = Replication.flatten(self.inputs['Level'].sv_get(deepcopy=False, default= 1))
		if isinstance(level,list):
			level = int(level[0])
		faceList = list(Replication.list_level_iter(faceList,level))
		faceList = [Replication.flatten(t) for t in faceList]
		outputs = []

		for t in range(len(faceList)):
			outputs.append(processItem(faceList[t], toleranceList[0]))
		self.outputs['Cell'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvCellByFaces)

def unregister():
    bpy.utils.unregister_class(SvCellByFaces)
