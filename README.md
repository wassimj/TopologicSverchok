This projects creates a Topologic python module from the Topologic C++ sources (available at https://github.com/NonManifoldTopology/Topologic.git)

### Install on Linux

Any recent distribution should have all the tools needed. The instructions below are for Debian-based distributions, but other distributions should have corresponding packages too. These instructions have been tested to work on Ubuntu Groovy Gorilla 2.10. *Please make sure you have updated your OS before attempting to install topologicPy*. In these instructions we assume *python3.8* and everythng is installed in */usr/local/lib*. Please change according to your python version.

1. **Create a working folder**: We will assume that you will install everything in ~/topologicbim
```
mkdir ~/topologicbim
cd ~/topologicbim
```

2. **Install dependencies**
 *UBUNTU (Tested)*
```
sudo apt-get install bzip2 unzip cmake make g++ git libgl-dev libglu-dev libpng-dev libxmu-dev libxi-dev libtbb-dev tcl-dev tk-dev zlib1g-dev libharfbuzz-dev libfreetype-dev libfreeimage-dev libocct-*-dev
```
if `libocct-*-dev` cannot be found while installing the dependencies, replace it with `libocct-foundation-dev libocct-data-exchange-dev`
 *Fedora (Suggested at OSArch.org, Untested)*
 ```
 sudo dnf install cmake gcc-c++ opencascade-devel libuuid-devel
 ```

3. **Install Topologic**
  *UBUNTU (Tested)*
```
git clone https://github.com/NonManifoldTopology/Topologic.git
cd Topologic
mkdir build
cd build
cmake ..
make
sudo make install
```
At the end of this process, libTopologicCore.so should exist in /usr/local/lib

  *Fedora (Suggested at OSArch.org, Untested)*
```
git clone https://github.com/NonManifoldTopology/Topologic.git
cd Topologic
mkdir BUILD
cd BUILD
cmake ..
make
sudo make install

This will likely install the library and headers to /usr/local so unless you have already edited your library path you need to do something like this:

sudo sh -c "echo /usr/local/lib >> /etc/ld.so.conf"
sudo ldconfig
```

4. **Install cppyy via pip**: This is needed at runtime by the topologic module:
```
sudo apt install python3-pip
sudo pip3 install cppyy
sudo ldconfig /usr/local/lib
```

5. **Install TopologicPy**
```
cd ~/topologicbim
git clone http://github.com/wassimj/TopologicPy
cd TopologicPy/cpython
python3 setup.py build
sudo python3 setup.py install
```

6. **Set the CPPYY_API_PATH**: edit the */etc/environment* file and add the following line
```
sudo gedit /etc/environment
```
Type the following into the file that opens
```
CPPYY_API_PATH="/usr/local/include/python3.8/CPyCppyy"
```
Save the file. Logout and log back in to continue

7. **Test**

Test in a Python 3 console:
```
python3
import topologic
import cppyy
```
If no error message appears, everything was correctly installed.

8. **Install for Blender 2.91 on Ubuntu 20.04 that uses the system's python3.8**
Remove any previous versions of Blender
```
sudo apt install blender
```
Make sure that your blender installation is using the system's python3.8

### Using the module

There is an [example.py](~/topologicbim/topologicPy/example.py) test file we have used to test the module. This example shows how you can use the Python/C++ to make calls directly to Topologic:

```
# import the topologic submodules
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Graph, Topology

# create a vertex
v1 = Vertex.ByCoordinates(0,0,0) 

# create another vertex
v2 = Vertex.ByCoordinates(20,20,20)

# create an edge from the two vertices
e1 = Edge.ByStartVertexEndVertex(v1, v2)

# retrieve the coordinate from the start vertex of e1
sv = e1.StartVertex()
print("   "+str([sv.X(), sv.Y(), sv.Z()]))

# retrieve the coordinate from the end vertex of e1
ev = e1.EndVertex()
print("   "+str([ev.X(), ev.Y(), ev.Z()]))

# retrieve the coordinates of the centroid of e1
cv = Topology.Centroid(e1)
print("   "+str([cv.X(), cv.Y(), cv.Z()]))
```
To test this file:
```
cd ~/topologicbim/topologicPy
python3 example.py
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
6. Print the coordinates of the centroid of e1:
   [10.0, 10.0, 10.0]
DONE
```
### How to install for Blender 2.92 from an Anaconda Virtual Environment

Blender 2.9.2 uses python 3.7.7. Therefore, you need to create a virtual environment and install cppyy and TopologicPy in that environment then replace Blender's python folder with this one. Here is one way to accomplish that using Anaconda

1. **Download and Install Anaconda** 

Download and install the individual version of Anaconda from https://www.anaconda.com/


2. **Create a virtual environment compatible with the version of python installed in Blender**

Open Blender, choose scripting and make note of the python version being used. We will assume it is python 3.7.7. Open a Terminal.app window and type the following:

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

Stay in the Terminal.app prompt and type the following:

```
cd ~/topologicbim/topologicPy/cpython
python setup.py build
sudo python setup.py install
```
After installation check the installed directory (in terminal), if installed directory path is in Python 3.8 use the below command to install into your created Python Blender377 environment. Remember to change 'USERNAME'
`sudo /home/USERNAME/anaconda3/envs/Blender377/bin/python setup.py install`

6. **Replace Blender's python folder**

Rename the folder of the Blender Python environment ```/Applications/Blender/Contents/Resources/2.92/python``` to something different like ```python-original```
Copy the anaconda virtual environment folder (e.g. ```~/opt/anaconda3/envs/Blender377```) to ```/Applications/Blender/Contents/Resources/2.92/``` and then re-name it to ``python``.
Start Blender
At the scripting command prompt in Blender, type the following script

```
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




### Troubleshooting

In case your distribution doesn't provide freetype:

```
cd /usr/src/
wget https://netactuate.dl.sourceforge.net/project/freetype/freetype2/2.9.1/freetype-2.9.1.tar.gz
tar xvf freetype-2.9.1.tar.gz
cd freetype-2.9.1
./configure && make && make install
```

In case your distribution doesn't provide freeimage:

```
cd /usr/src/
wget https://managedway.dl.sourceforge.net/project/freeimage/Source%20Distribution/3.18.0/FreeImage3180.zip
unzip FreeImage3180.zip
cd FreeImage && \
	make && \
	make install
```

In case your distribution doesn't provide opencascade (occt):

```
cd /usr/src/
wget https://github.com/tpaviot/oce/releases/download/official-upstream-packages/opencascade-7.4.0.tgz
tar xvf opencascade-7.4.0.tgz
cd opencascade-7.4.0
mkdir build && \
	cd build && \
	cmake .. && \
	make && \
	make install
```






