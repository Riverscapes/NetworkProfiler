import unittest

from NetworkProfiler.profiler import Profile
from utilities import get_qgis_app

QGIS_APP = get_qgis_app()

from qgis.core import QgsVectorLayer
from os import path

class TestProfiler(unittest.TestCase):

    def setUp(self):
        """Runs before each test."""
        uri = path.join(path.dirname(__file__),'data','StressTest.shp')
        self.vlayer = QgsVectorLayer(uri, "StressTest_Layer", "ogr")
        self.nxProfile = Profile(self.vlayer, None)



    def tearDown(self):
        """Runs after each test."""
        # self.dialog = None

    def test_linestringZType(self):
        """
        Make sure we can open Linestring Z types
        :return:
        """
        uri = path.join(path.dirname(__file__), 'data', 'LineString.shp')
        uriZ = path.join(path.dirname(__file__),'data','LineStringZ.shp')
        uriM = path.join(path.dirname(__file__), 'data', 'LineStringM.shp')
        uriZM = path.join(path.dirname(__file__), 'data', 'LineStringZM.shp')
        vlayer = QgsVectorLayer(uri, "StressTest_Layer", "ogr")
        vlayerZ = QgsVectorLayer(uri, "StressTest_Layer", "ogr")
        vlayerM = QgsVectorLayer(uri, "StressTest_Layer", "ogr")
        vlayerZM = QgsVectorLayer(uri, "StressTest_Layer", "ogr")
        lszProfile = Profile(vlayer)
        lszProfileZ = Profile(vlayerZ)
        lszProfileM = Profile(vlayerM)
        lszProfileZM = Profile(vlayerZM)

        self.assertTupleEqual(lszProfile.findEdgewithID(0), lszProfileZ.findEdgewithID(0))
        self.assertTupleEqual(lszProfile.findEdgewithID(0), lszProfileM.findEdgewithID(0))
        self.assertTupleEqual(lszProfile.findEdgewithID(0), lszProfileZM.findEdgewithID(0))

    def test_getPathEdgeIds(self):
        from NetworkProfiler.profiler import EdgeObj
        self.nxProfile.paths = [[
            EdgeObj(((0,1), (2,3)), [1]),
            EdgeObj(((2,3), (4,5)), [2]),
            EdgeObj(((4,5), (6,7)), [3]),
        ]]
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[1,2,3]])

    def test_findnodewithID(self):
        ptA = self.nxProfile.findEdgewithID(22)
        ptNone = self.nxProfile.findEdgewithID(9999)

        self.assertAlmostEqual(ptA.edge[0][0], -2.53887357711)
        self.assertAlmostEqual(ptA.edge[0][1],  1.56345777511)
        self.assertAlmostEqual(ptA.edge[1][0], -2.65314254760)
        self.assertAlmostEqual(ptA.edge[1][1],  1.02476119995)

        self.assertIsNone(ptNone)

    # def test_writeCSV(self):
    #     self.fail()
    #
    def test_pathfinder(self):
        """
        We test the positive cases first
        :return:
        """

        # Test a single path. This is the simplest case
        self.nxProfile.pathfinder(8, 10)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[8,9,10]])

        # Double Path
        self.nxProfile.pathfinder(22, 28)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[22, 23, 26, 27, 28], [22, 24, 25, 27, 28]])

        # Triple Path
        self.nxProfile.pathfinder(29, 34)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[29, 30, 33, 34], [29, 31, 33, 34], [29, 32, 34]])

        # Second Triple Path
        self.nxProfile.pathfinder(30, 34)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[30, 33, 34]])

        # Two inlets, one outlet
        self.nxProfile.pathfinder(4, 7)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[4,5,7]])

        # Crazy self-intersecting path
        self.nxProfile.pathfinder(3, 2)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[3, 0, 1, 2]])

        # Circle
        self.nxProfile.pathfinder(13, 15)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[13, 14, 15]])

        # Start to outflow point
        self.nxProfile.pathfinder(8)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[8,9,10]])

        # Test "find outflow" with multiple paths
        self.nxProfile.pathfinder(22)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[22,23,26,27,28],[22,24,25,27,28]])

        # Test "find outflow" with multiple outflows
        self.nxProfile.pathfinder(35)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [[35,36,37],[35,38,39]])


    def test_reverse_pathfinder(self):
        """
        If we pass in a backwards path then reverse it
        :return:
        """

        # Test a single path. Thisse is the simplest case

        self.assertFalse(self.nxProfile.reversible)
        self.nxProfile.pathfinder(8, 10)
        self.assertFalse(self.nxProfile.reversible)
        self.nxProfile.pathfinder(10, 8)
        self.assertTrue(self.nxProfile.reversible)

    def test_segLength(self):
        self.assertEqual(self.nxProfile._segLength(30), 0.48666221658771897)

    def test_pathLength(self):
        self.nxProfile.pathfinder(8, 10)
        manual = self.nxProfile._segLength(8) + self.nxProfile._segLength(9) + self.nxProfile._segLength(10)
        self.assertEqual(self.nxProfile._pathLength(self.nxProfile.paths[0]), manual)

    def test_chooseEdges(self):
        print "yay"

    def test_choosebylength(self):
        self.nxProfile.pathfinder(29, 34)

        shortest = self.nxProfile._choosebylength()
        self.assertListEqual(self.nxProfile.getPathEdgeIds(shortest), [29, 30, 33, 34])


if __name__ == '__main__':
    unittest.main()
