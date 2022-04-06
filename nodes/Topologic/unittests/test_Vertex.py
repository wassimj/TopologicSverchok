import unittest
import sys
sys.path.append(r"C:\Users\wassimj\AppData\Roaming\Blender Foundation\Blender\3.0\scripts\addons\os-win-occt7.5\topologicsverchok\site-packages\topologic")
from topologic import Vertex

class TestVertex(unittest.TestCase):
	def test_create(self):
		v = Vertex.ByCoordinates(0,0,0)
		assertIsInstance(v, Vertex)

if __name__ == '__main__':
	unittest.main()