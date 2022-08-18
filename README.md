# TopologicSverchok

![TopologicSververchok-logo](assets/TopologicSverchok-Logo-500x250.png)

**TopologicSverchok** is a [Sverchok](http://nortikin.github.io/sverchok/) implementation of [Topologic](https://topologic.app) both running within [Blender](https://www.blender.org/).

[**Topologic**](https://topologic.app/) is a software modeling library enabling hierarchical and topological representations of architectural spaces, buildings and artefacts through non-manifold topology. 

[**Sverchok**](http://nortikin.github.io/sverchok/) is a powerful Blender Addon parametric tool for architects, allowing geometry to be programmed visually with nodes. 

[**Blender**]() is a FOSS 3D creation suite. It supports the entirety of the 3D pipeline—modeling, rigging, animation, simulation, rendering, compositing and motion tracking, even video editing and game creation. It has an API for Python scripting for customization and writing specialized tools such as TopologicSverchok.

## Prerequisites

TopologicSverchok requires the following software to be installed:

* [Blender](https://www.blender.org/) >= v3.2
* [Sverchok](https://github.com/nortikin/sverchok/) >= 1.1.0
* [numpy](https://numpy.org/) >= 1.22.4

### Optional Dependencies

The installation of these optional python modules will activate additional TopologicSverchok nodes. These python modules can be installed in the `site-packages` subdirectory. 

```bash
    TopologicSverchok
    └── site-packages
```

Familiarity with python module installation is needed.

<details>
<summary>
<b>Expand to view optional dependencies</b>
</summary>

* [ifcopenshell](http://ifcopenshell.org/) (recommended that you install BlenderBIM](https://blenderbim.org/) and [Homemaker](https://github.com/brunopostle/homemaker-addon))
* [ipfshttpclient](https://pypi.org/project/ipfshttpclient/) >= 0.7.0
* [web3](https://web3py.readthedocs.io/en/stable/) >=5.30.0
* [openstudio](https://openstudio.net/) >= 3.4.0
* [lbt-ladybug](https://pypi.org/project/lbt-ladybug/) >= 0.25.161
* [lbt-honeybee](https://pypi.org/project/lbt-honeybee/) >= 0.6.12
* [honeybee-energy](https://pypi.org/project/honeybee-energy/) >= 1.91.49
* [json](https://docs.python.org/3/library/json.html) >= 2.0.9impor
* [py2neo](https://py2neo.org/) >= 2021.2.3
* [pyvisgraph](https://github.com/TaipanRex/pyvisgraph) >= 0.2.1
* [specklepy](https://github.com/specklesystems/specklepy) >= 2.7.6
* [pandas](https://pandas.pydata.org/) >= 1.4.2
* [scipy](https://scipy.org/) >= 1.8.1
* [dgl](https://github.com/dmlc/dgl) >= 0.8.2

</details>

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
