from unittest import TestCase

from NetworkProfiler.profiler import Profile
from utilities import get_qgis_app

QGIS_APP = get_qgis_app()

from qgis.core import QgsVectorLayer
from os import path

class TestProfiler(TestCase):

    def setUp(self):
        """Runs before each test."""
        uri = path.join(path.dirname(__file__),'data','LineString.shp')
        self.vlayer = QgsVectorLayer(uri, "LineString_Layer", "ogr")
        self.nxProfile = Profile(self.vlayer)

    def tearDown(self):
        """Runs after each test."""
        # self.dialog = None

    def test_linestringZType(self):
        """
        Make sure we can open Linestring Z types
        :return:
        """
        uri = path.join(path.dirname(__file__),'data','LineStringZ.shp')
        vlayer2 = QgsVectorLayer(uri, "LineStringZ_Layer", "ogr")
        lszProfile = Profile(self.vlayer)

        self.assertTupleEqual(self.nxProfile.findEdgewithID(22), lszProfile.findEdgewithID(22))

    def test_getPathEdgeIds(self):
        from NetworkProfiler.profiler import EdgeObj
        self.nxProfile.paths = [[
            EdgeObj(((0,1), (2,3)), 1),
            EdgeObj(((2,3), (4,5)), 2),
            EdgeObj(((4,5), (6,7)), 3),
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

        # Now test it backward
        self.nxProfile.pathfinder(10, 8)
        self.assertListEqual(self.nxProfile.getPathEdgeIds(), [])

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


    # def test_calcfields(self):
    #
    #     self.nxProfile.calcfields()
