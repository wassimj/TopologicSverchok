(For installation instructions, scroll to the bottom of the page)
<p align="center">
<a href="http://nortikin.github.io/sverchok/">
<img src="https://topologic.app/wp-content/uploads/2018/10/Topologic-Logo-250x250.png" width="250" title="Topologic">
</a>
</p>

# TopologicSverchok
TopologicSverchok is a Sverchok implementation of Topologic which is a software modelling library enabling hierarchical and topological representations of architectural spaces, buildings and artefacts through non-manifold topology. Sverchok (https://github.com/nortikin/sverchok). Sverchok is a powerful parametric tool for architects, allowing geometry to be programmed visually with nodes. 

The project website is located here: https://topologic.app/

### Installation Instructions
Prerequistes:
TopologicSverchok requires these modules to be installed for it to function properly
1. Sverchok
2. numpy

Optional python modules:
The installation of these optional python modules will activate additional TopologicSverchok nodes. These python modules can be installed in the site-packages folder inside the topologicsverchok folder. Familiarity with python module installation is needed.
1. ifcopenshell (recommended that you install BlenderBIM and Homemaker)
2. ipfshttpclient
3. web3
4. openstudio
5. honeybee
6. honeybee-energy
7. ladybug
8. json
9. py2neo
10. pyvisgraph
11. specklepy
12. numpy
13. pandas
14. scipy
15. dgl

Download the latest Release binaries from the Releases link found on the right side of this page (https://github.com/wassimj/TopologicSverchok/releases).
1. After you download the ZIP file, do NOT unzip.
2. Launch Blender
3. Go to Edit -> Preferences...
4. Select Add-ons in the left side column
5. Select Install... from the top row
6. Locate your downloaded ZIP file and select it
7. Once Topologic appears in the list of Add-ons, click the empty check box to activate it
8. Close the Preferences.. window
9. Switch over to the Scripting workspace
10. Open the Editor Type pull-down menu icon in the top-left corner and witch to sverchok node
11. Select the + New button to start a new sverchok node tree
12. The Topologic nodes should now be available under the Add menu