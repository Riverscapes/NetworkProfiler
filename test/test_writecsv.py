from unittest import TestCase

from NetworkProfiler.profiler import Profile
from utilities import get_qgis_app

QGIS_APP = get_qgis_app()

from qgis.core import QgsVectorLayer
from os import path

class TestWriteCSV(TestCase):

    def setUp(self):
        """Runs before each test."""
        uri = path.join(path.dirname(__file__),'data','StressTest.shp')
        self.vlayer = QgsVectorLayer(uri, "StressTest_Layer", "ogr")
        self.nxProfile = Profile(self.vlayer, None)
        self.nxProfile.pathfinder(8, 10)
        #     ['DateTime', 'Date', 'Time', 'RealField', 'IntField', 'StringFiel', 'PathName', 'PathName2']


    def tearDown(self):
        """Runs after each test."""
        # self.dialog = None

    def test_basic_write(self):
        # Test a single path. This is the simplest case
        cols = ['DateTime', 'Date', 'Time', 'RealField', 'IntField', 'StringFiel', 'PathName', 'PathName2']
        self.nxProfile.generateCSV(cols)
        self.assertEqual(len(self.nxProfile.results), 3)

        # Check that our keys have the same elements
        icols = cols + self.nxProfile.calccols + [self.nxProfile.idField, 'Wkt']
        rcols = self.nxProfile.results[0].keys()
        self.assertTrue(all(c in icols for c in rcols))
        self.assertTrue(all(c in rcols for c in icols))

    def test_colsubset(self):
        cols = ['PathName', 'PathName2']
        self.nxProfile.generateCSV(cols)
        self.assertEqual(len(self.nxProfile.results), 3)

        # Check that our keys have the same elements
        icols = cols + self.nxProfile.calccols + [self.nxProfile.idField, 'Wkt']
        rcols = self.nxProfile.results[0].keys()
        self.assertTrue(all(c in icols for c in rcols))
        self.assertTrue(all(c in rcols for c in icols))



