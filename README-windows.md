This projects creates a Topologic python module from the Topologic C++ sources (available at https://github.com/NonManifoldTopology/Topologic.git)

### Install on Windows 10

The instructions below are for Microsoft Windows 10. In these instructions we assume *Visual Studio Community 2017* *opencascade 7.4.0* and *python3.8.8*. We also assume that your account has Adminstrator priviliges.

1. **Create a topologicbim working folder**: We will assume that your home folder is called *homefolder* and you will install everything in *homefolder*/topologicbim

2. **Install Visual Studio Community 2017**

**WARNING:** cppyy 1.9.x only works with *Visual Studio Community 2017* 

Download from https://visualstudio.microsoft.com/vs/older-downloads/
Make sure you check the box for Desktop Development with C++ 

3. **Install Git**

Download from https://git-scm.com/download/win

4. **Install Python 3.8.8**

**WARNING:** Do not install from the Microsoft Store.

Download from https://www.python.org/downloads/windows/

**WARNING:** When installing python make sure you tick the box on the installation screen to add python to the path. For example see the image below:

![python installation window](https://blog.uvm.edu/tbplante/files/2020/07/path-install.png)

5. **Install cmake 3.19.5**

Download from https://cmake.org/download/

Scroll down and look for the latest release and choose the *Windows win64-x64 Installer* 

6. **Install cppyy via pip**: This is needed at runtime by the topologic module:

Go to the Start Menu in the lower left corner Search for the Visual Studio 2017 Folder and expand it Choose *x64 Native Tools Command Prompt.* In the window that appears type:
```
pip install cppyy
```
If the command pip is not found, install pip
```
cd C:/Users/*homefolder*/topologicbim/
python get-pip.py
pip --version
```
If the above is successful re-issue the pip command:
```
pip install cppyy
```

7. **Install Opencascade 7.4.0**

Download from https://old.opencascade.com/content/previous-releases

Choose  *Windows installer VC++ 2017 64 bit: opencascade-7.4.0-vc14-64.exe (237 061 168 bytes)*

This will automatically install opencascade in:
```
C:/OpenCASCADE-7.4.0-vc14-64
```
Do **NOT** change the location and name of this folder.

8. **Fix a file in the Opencascade installation**

Unfortunately, there is a small change needed in the opencascade files for TopologicPy to work. The file that needs to be edited in opencascade is:
```
C:\OpenCASCADE-7.4.0-vc14-64\opencascade-7.4.0\inc\Standard_Macro.hxx.
```
You need to change line 67 from 
```
#if defined(__has_cpp_attribute)
```
to 
```
 #if defined(__has_cpp_attribute) && !defined(__CLING__)
```

9. **Install Topologic**

Go to the Start Menu in the lower left corner
Search for the Visual Studio 2017 Folder and expand it
Choose *x64 Native Tools Command Prompt*
In the window that appears type:
```
cd C:/Users/*homefolder*/topologicbim
git clone https://github.com/NonManifoldTopology/Topologic.git
cd Topologic
WindowsBuild.bat
```
10. **Set the Environment Variable**

A window will open with a folder that has all the DLL files. Copy the path of this folder and add it to the **PATH** environment variable:
```
. In Search, search for and then select: System (Control Panel)
. Click the Advanced system settings link.
. Click Environment Variables. ...
. In the Edit System Variable (or New System Variable) window, add the folder to the PATH environment variable.
```
11. **Download TopologicPy**

stay in the same window
```
cd C:/Users/*homefolder*/topologicbim
git clone https://github.com/wassimj/topologicPy.git
```
12. **Fix the win_prefix**

Edit the ```C:/Users/*homefolder*/topologicbim/topologicPy/cpython/topologic/__init__.py``` file and look for the *win_prefix*
Set it to the location of the Topologic installation (e.g. win_prefix = "C:/Users/*homefolder*/topologicbim/Topologic")

13. **Install TopologicPy**

```
cd C:/Users/*homefolder*/topologicbim/topologicPy/cpython
python setup.py build
python setup.py install
```

14. **Test**

Test:
```
cd C:/Users/*homefolder*/topologicbim/topologicPy/
python example.py
```
You should see the following as an output:
```
START
1. Create Vertex (v1) at 0 0 0
2. Create Vertex (v2) at 20 20 20
3. Create an Edge (e1) connecting v1 to v2
4. Print the coordinates of the start vertext of e1:
   [0.0, 0.0, 0.0]
5. Print the coordinates of the end vertext of e1:
   [20.0, 20.0, 20.0]
5. Print the coordinates of the centroid of e1:
   [10.0, 10.0, 10.0]
DONE
```
### How to install for Blender

Blender 2.9.2 uses python 3.7.7. Therefore, it is advisable to create a virtual environment and install cppyy and TopologicPy in that environment. You can then simply point Blender's python to use the files in that virtual envrionment. Here is one way to accomplish that using Anaconda

1. **Download Anaconda** 

Download the individual version of Anaconda from https://www.anaconda.com/products

2. **Open the CMD.exe Prompt**

After install, select the CMD.exe Prompt from the *Home* tab in the *Anaconda Navigator*

3. **Create a virtual environment compatible with the version of python installed in Blender**

Open Blender, choose scripting and make note of the python version being used. We will assume it is python 3.7.7. Go back to the Anaconda CMD.exe Prompt and type the following:

```
conda create --name Blender377 python=3.7.7
conda activate Blender377
```

4. **Install cppyy**

Stay in the Anaconda CMD.exe Prompt and type the following:

```
pip install cppyy
```

5. **Re-install TopologicPy**

Stay in the Anaconda CMD.exe Prompt and type the following:

```
cd C:/Users/*homefolder*/topologicbim/topologicPy/cpython
python setup.py build
python setup.py install
```
6. **Test in Blender**

At the scripting command prompt in Blender, type the following script.

**WARNING: Replace the topologic egg name with the correct and latest installed version!**

Make note of the anaconda virtual environments folder path. This may be something like:

```
C:\\ProgramData\anaconda3\envs\Blender377\lib\site-packages
```
and the path to the topologic egg may then be
```
C:\\ProgramData\anaconda3\envs\Blender377\lib\site-packages\\topologic-0.4-py3.7.egg
```

```
import sys
sys.path.append("**path to site-packages folder from above**")
sys.path.append("**path to topologic egg from above**")
import cppyy
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph, Dictionary

v1 = Vertex.ByCoordinates(0,0,0)
v2 = Vertex.ByCoordinates(10,10,10)
e1 = Edge.ByStartVertexEndVertex(v1, v2)
c1 = e1.Centroid()
print([c1.X(), c1.Y(), c1.Z()])
```

If you see the following, then all is fine:

```
[5.0, 5.0, 5.0]
```
