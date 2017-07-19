import unittest
from NetworkProfiler.profiler import Profile
from utilities import get_qgis_app

QGIS_APP = get_qgis_app()

from qgis.core import QgsVectorLayer
from os import path

class TestPathChoice(unittest.TestCase):

    def setUp(self):
        """
        Runs before each test.
        It's easier just to load a sample file than to write a bunch of mocking
        """

        uri = path.join(path.dirname(__file__),'data','StressTest.shp')
        self.vlayer = QgsVectorLayer(uri, "StressTest_Layer", "ogr")
        self.profile = Profile(self.vlayer, None)
        self.testchoices = [
            [self.profile.findEdgewithID(id) for id in [ 30, 31, 32 ]],
            [self.profile.findEdgewithID(id) for id in [ 36, 38]]
        ]

    def test_choose_shortest(self):
        """
        We test the positive cases first
        :return:
        """
        self.profile.choice = Profile.CHOICE_SHORTEST
        self.profile.pathfinder(29, 34)

        shortest = self.profile._choosebylength()
        self.assertListEqual(self.profile.getPathEdgeIds(shortest), [29, 30, 33, 34])

    def test_choose_field_not_empty(self):
        """
        We test the positive cases first
        :return:
        """
        self.profile.choice = Profile.CHOICE_FIELD_NOT_EMPTY

        self.profile.fieldname = "PathName2"
        self.assertEqual(self.profile._chooseEdges(self.testchoices[1])[0].fids[0], 36)

    def test_choose_field_value(self):
        """
        We test the positive cases first
        :return:
        """
        self.profile.choice = Profile.CHOICE_FIELD_VALUE
        self.profile.fieldname = "PathName"
        self.profile.fieldval = "A"
        self.assertEqual(self.profile._chooseEdges(self.testchoices[0])[0].fids[0], 30)

        self.profile.fieldval = "B"
        self.assertEqual(self.profile._chooseEdges(self.testchoices[0])[0].fids[0], 32)

        self.profile.fieldval = "C"
        self.assertEqual(self.profile._chooseEdges(self.testchoices[0])[0].fids[0], 31)

        # No Good Choice
        self.profile.fieldval = "D"
        self.assertEqual(self.profile._chooseEdges(self.testchoices[0]), self.testchoices[0])

        # When you don't pass in a value
        self.profile.fieldname = "PathName"
        self.profile.fieldval = None
        self.assertEqual(self.profile._chooseEdges(self.testchoices[0]), self.testchoices[0])

        # When you pass in a field that's not there
        self.profile.fieldname = "PathName"
        self.profile.fieldval = "Booya"
        self.assertEqual(self.profile._chooseEdges(self.testchoices[0]), self.testchoices[0])

    def test_choose_field_not_value(self):
        """
        We test the positive cases first
        :return:
        """
        self.profile.choice = Profile.CHOICE_FIELD_NOT_VALUE
        self.profile.fieldname = "PathName"
        self.profile.fieldval = "A"

        chosenpathA = self.profile._chooseEdges(self.testchoices[0])
        self.assertEqual(self.profile.getPathEdgeIds(chosenpathA), [31,32])

        self.profile.fieldval = "B"
        chosenpathB = self.profile._chooseEdges(self.testchoices[0])
        self.assertEqual(self.profile.getPathEdgeIds(chosenpathB), [30,31])

        self.profile.fieldval = "C"
        chosenpathC = self.profile._chooseEdges(self.testchoices[0])
        self.assertEqual(self.profile.getPathEdgeIds(chosenpathC), [30,32])

    def test_wrongpath(self):
        """
        Test what happens when there's a good choice that leads to a bad place
        :return:
        """
        self.profile.choice = Profile.CHOICE_FIELD_NOT_VALUE
        self.profile.fieldname = "PathName"
        self.profile.fieldval = "B"
        self.profile.pathfinder(45, 37)

        self.assertEqual(self.profile.getPathEdgeIds(self.profile.paths[0]), [45, 35, 36, 37])


if __name__ == '__main__':
    unittest.main()