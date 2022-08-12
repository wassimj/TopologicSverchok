# TopologicSverchok

![TopologicSververchok-logo](assets/TopologicSverchok-Logo-500x250.png)

**TopologicSverchok** is a [Sverchok](http://nortikin.github.io/sverchok/) implementation of [Topologic](https://topologic.app). 

[**Topologic**](https://topologic.app/) is a software modeling library enabling hierarchical and topological representations of architectural spaces, buildings and artefacts through non-manifold topology. 

[**Sverchok**](http://nortikin.github.io/sverchok/) is a powerful parametric tool for architects, allowing geometry to be programmed visually with nodes. 


## Prerequisites

TopologicSverchok requires the following modules to be installed:

* [Blender](https://www.blender.org/)
* [Sverchok](https://github.com/nortikin/sverchok/)
* [numpy](https://numpy.org/)

### Optional python modules:

The installation of these optional python modules will activate additional TopologicSverchok nodes. These python modules can be installed in the site-packages folder inside the topologicsverchok folder. Familiarity with python module installation is needed.

* [ifcopenshell]() (recommended that you install BlenderBIM]() and [Homemaker]())
* [ipfshttpclient](https://pypi.org/project/ipfshttpclient/)
* [web3](https://web3py.readthedocs.io/en/stable/)
* [openstudio](https://openstudio.net/)
* [ladybug](https://www.ladybug.tools/)
* [honeybee](https://www.ladybug.tools/honeybee.html)
* [honeybee-energy](https://github.com/ladybug-tools/honeybee-energy)
* [json](https://docs.python.org/3/library/json.html)
* [py2neo](https://py2neo.org/)
* [pyvisgraph](https://github.com/TaipanRex/pyvisgraph)
* [specklepy](https://github.com/specklesystems/specklepy)
* [numpy](https://numpy.org/)
* [pandas](https://pandas.pydata.org/))
* [scipy](https://scipy.org/)
* [dgl](https://github.com/dmlc/dgl)

### Binaries

Download the latest Release binaries from the Releases link found on the right side of this [page](https://github.com/wassimj/TopologicSverchok/releases).

## Installation

1. After you download the ZIP file, do NOT unzip.
1. Launch Blender
1. Go to `Edit` -> `Preferences...`
1. Select Add-ons in the left side column
1. Select `Install...` from the top row
1. Locate your downloaded ZIP file and select it
1. Once Topologic appears in the list of Add-ons, click the empty check box to activate it
1. Close the `Preferences..` window
1. Switch over to the Scripting workspace
1. Open the Editor Type pull-down menu icon in the top-left corner and witch to sverchok node
1. Select the `+ New` button to start a new sverchok node tree
1. The Topologic nodes should now be available under the Add menu
