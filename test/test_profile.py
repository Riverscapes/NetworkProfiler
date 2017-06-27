from unittest import TestCase
from profiler import Profile

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()

from qgis.core import QgsVectorLayer, QgsMapLayerRegistry
from os import path

class TestProfiler(TestCase):

    def setUp(self):
        """Runs before each test."""
        uri = path.join(path.dirname(__file__),'data','stresstest.shp')
        self.vlayer = QgsVectorLayer(uri, "StressTest", "ogr")
        self.nxProfile = Profile(self.vlayer)

    def tearDown(self):
        """Runs after each test."""
        # self.dialog = None

    def test_findnodewithID(self):
        ptA = self.nxProfile.findnodewithID(22)

        ptNone = self.nxProfile.findnodewithID(9999)


        self.assertAlmostEqual(ptA[0][0], -2.53887357711)
        self.assertAlmostEqual(ptA[0][1],  1.56345777511)
        self.assertAlmostEqual(ptA[1][0], -2.65314254760)
        self.assertAlmostEqual(ptA[1][1],  1.02476119995)

        self.assertIsNone(ptNone)

    # def test_writeCSV(self):
    #     self.fail()
    #
    def test_pathfinder(self):
        # Test a single path. This is the simplest case
        singlePath = self.nxProfile.pathfinder(8, 10)
        # Start to outflow point
        singlePath = self.nxProfile.pathfinder(8)
        # Now test it backward
        singlePathBackward = self.nxProfile.pathfinder(10, 8)

        # Double Path
        singlePathBackward = self.nxProfile.pathfinder(22, 28)


        # Crazy self-intersecting path
        singlePathBackward = self.nxProfile.pathfinder(3, 2)

        # Two inlets, one outlet
        singlePathBackward = self.nxProfile.pathfinder(4, 7)

        # Circle
        singlePathBackward = self.nxProfile.pathfinder(13, 15)

        self.fail()

    # def test_calcfields(self):
    #
    #     self.nxProfile.calcfields()
