import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import time

import sys, subprocess, pkg_resources

dependency_list = ['ipfshttpclient',
            'ladybug',
            'honeybee-energy',
            'honeybee-radiance',
            'openstudio',
            'py2neo',
            'pyvisgraph',
            'numpy',
            'pandas',
            'scipy',
            'torch',
            'networkx',
            'tqdm',
            'sklearn',
            'dgl',
            'plotly',
            'specklepy']

def install_dependency(module):
    # upgrade pip
    call = [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip']
    print(f"Installing {module}")
    if module == 'dgl':
        call = [sys.executable, '-m', 'pip', 'install', module, 'dglgo', '-f', 'https://data.dgl.ai/wheels/repo.html', '--upgrade', '-t', sys.path[0]]
    elif module == 'ladybug':
        call = [sys.executable, '-m', 'pip', 'install', 'ladybug-core', '-U', '--upgrade', '-t', sys.path[0]]
    elif module == 'honeybee-energy':
        call = [sys.executable, '-m', 'pip', 'install', 'honeybee-energy', '-U', '--upgrade', '-t', sys.path[0]]
    elif module == 'honeybee-radiance':
        call = [sys.executable, '-m', 'pip', 'install', 'honeybee-radiance', '-U', '--upgrade', '-t', sys.path[0]]
    else:
        call = [sys.executable, '-m', 'pip', 'install', module, '-t', sys.path[0]]
    subprocess.run(call)

def checkInstallation(module):
    returnValue = False
    if module == 'honeybee-energy':
        try:
            import honeybee
            import honeybee_energy
            from honeybee.model import Model
            returnValue = True
        except:
            pass
    elif module == 'honeybee-radiance':
        try:
            import honeybee_radiance
            returnValue = True
        except:
            pass
    else:
        try:
            import module
            returnValue = True
        except:
            pass

def processItem():
    status = []
    installed_packages = {i.key: i.version for i in pkg_resources.working_set}
    flag = ''
    for module in dependency_list:
        if module in installed_packages.keys():
            flag = 'Already installed'
        else:
            try:
                install_dependency(module)
                flag = 'Successfully installed'
            except:
                if checkInstallation(module):
                    flag = 'Successfully installed'
                else:
                    flag = 'Failed to insall'
                flag = 'Failed to install'
        status.append(f"{module}: {flag}.")
    return status

class SvTopologicInstallDependencies(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Installs Topologic's optional Python dependencies
	"""
	bl_idname = 'SvTopologicInstallDependencies'
	bl_label = 'Topologic.InstallDependencies'
	
	def sv_init(self, context):
		self.outputs.new('SvStringsSocket', 'Status')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		status = processItem()
		self.outputs['Status'].sv_set(status)
		end = time.time()
		print("Topologic.InstallDependencies Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvTopologicInstallDependencies)

def unregister():
    bpy.utils.unregister_class(SvTopologicInstallDependencies)
