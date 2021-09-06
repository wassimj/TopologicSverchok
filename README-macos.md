This projects creates a Topologic python module from the Topologic C++ sources (available at https://github.com/NonManifoldTopology/Topologic.git)

### Install on MacOS

These instructions have been tested to work on MacOS 10.15.7 Catalina. *Please make sure you have updated your OS before attempting to install topologicPy*. In these instructions we assume *python3.8* and everythng is installed in */usr/local/lib*. Please change according to your python version.

1. **Download XCode from the App Store**

2. **Download Brew**

Open a Terminal.app window and type the following:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

3. **Download OpenCascade** (Time consuming step)

Open a Terminal.app window and type the following:
```
brew tap-new $USER/local-opencascade
brew extract --version=7.4.0 opencascade $USER/local-opencascade
brew install opencascade@7.4.0
```

4. **Create a working folder**

We will assume that you will install everything in ~/topologicbim
```
mkdir ~/topologicbim
cd ~/topologicbim
```

5. **Install Topologic**
```
git clone https://github.com/NonManifoldTopology/Topologic.git
cd Topologic
mkdir build
cd build
cmake ..
make
sudo make install
cd ../..
```

4. **Install cppyy via pip**: This is needed at runtime by the topologic module:
```
sudo -H pip3 install cppyy
```

5. **Install TopologicPy**
```
cd ~/topologicbim
git clone http://github.com/wassimj/topologicPy
cd topologicPy/cpython
python3 setup.py build
sudo python3 setup.py install
```
7. **Test**

Test in a Python 3 console:
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

### Troubleshooting
If the example doesn't work for you, you may need to add /usr/local/lib to your path. In a Terminal.app window type the following:
```
sudo nano /etc/paths
```
Add /usr/local/lib as the last line, save and quit and try again.

### How to install for Blender

Blender 2.9.2 uses python 3.7.7. Therefore, you need to create a virtual environment and install cppyy and TopologicPy in that environment then replace Blender's python folder with this one. Here is one way to accomplish that using Anaconda

1. **Download Anaconda** 

Download the individual version of Anaconda from https://www.anaconda.com/products


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



