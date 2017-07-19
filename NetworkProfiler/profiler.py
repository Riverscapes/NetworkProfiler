
import networkx as nx
import ogr
import copy
from qgis.core import *
import logging
from collections import namedtuple
from shapely import wkb


"""
We invented a special kind of tuple to handle all the different properties of an "Edge"
"""

EdgeObj = namedtuple('EdgeObj', ['edge', 'fids'])


class Profile():

    CHOICE_SHORTEST = "Choose the path with the shortest length"
    CHOICE_FIELD_NOT_EMPTY = "Choose path where a field is not empty"
    CHOICE_FIELD_VALUE = "Choose field that has a value"
    CHOICE_FIELD_NOT_VALUE = "Choose field that does NOT have value"

    def __init__(self, shpLayer, choice=None, fieldname=None, fieldval=None, msgcallback=None):
        """
        Profile a network from startID to endID

        If no outID is specified we go and found the outflow point and use that
        """

        self.logger = logging.getLogger('Profile')
        self.msgcallback = msgcallback
        self.reversible = False
        self.idField = "_FID_"
        self.metalogs = []
        self.pathmsgs = []

        self.paths = []

        self.fromEdge = None
        self.toEdges = []

        self.features = {}
        self.cols = []
        self.calccols = []
        self.csvkeys = []

        self.results = []

        # Convert QgsLayer to NX graph
        self._qgsLayertoNX(shpLayer, simplify=True)

        self.choice = Profile.CHOICE_SHORTEST if choice is None else choice

        self.fieldname = fieldname
        self.fieldval = fieldval

        if fieldname is None and choice == Profile.CHOICE_FIELD_VALUE or choice == Profile.CHOICE_FIELD_NOT_EMPTY:
            raise Exception("ERROR: If you want to use a field option you need to specify a field")

        if fieldval is None and choice == Profile.CHOICE_FIELD_VALUE:
            raise Exception("ERROR: If you your path choice involves a field value you must provide one")

    def getFromID(self):
        return self.fromEdge.fids[0] if self.fromEdge is not None else None

    def getToID(self):
        return self.toEdges[0].fids[0] if len(self.toEdges) > 0 else None

    def getPathEdgeIds(self, path=None):
        """
        Get the FIDs of all the paths in the object
        :return:
        """
        ids = []

        if path is None:
            for p in self.paths:
                ids.append([idx.fids[0] for idx in p])
        else:
            ids = [idx.fids[0] for idx in path]

        return ids

    def calcfields(self, edges):
        """
        These are fields that need to be calculated.
        :param edges:
        :return:
        """
        calcdict = {}

        cummulativelength = 0

        for idx, edge in enumerate(edges):
            fid = edge.fids[0]
            attrCalc = {}
            attrCalc['ProfileCalculatedLength'] = self._segLength(fid)
            cummulativelength += attrCalc['ProfileCalculatedLength']
            attrCalc['ProfileCummulativeLength'] = cummulativelength
            attrCalc['ProfileID'] = idx + 1

            calcdict[fid] = attrCalc

        self.calccols = calcdict[calcdict.keys()[0]].keys()
        return calcdict

    def pathfinder(self, inID, outID=None):
        """
        Find the shortest path between two nodes or just one node and the outflow
        :param G:
        :param inID:
        :param outID:
        :return:
        """
        self.paths = []
        self.pathmsgs = []
        self.toEdges = []
        self.fromEdge = None
        self.reversible = False
        self.fromEdge = self.findEdgewithID(inID)

        if not self.fromEdge:
            raise Exception("Could not find start ID: {} in network.".format(inID))

        if outID:
            outIDs = [outID]
            toEdge = self.findEdgewithID(outID)
            if not toEdge:
                raise Exception("Could not find end ID: {} in network.".format(outID))
            self.toEdges = [toEdge]
        else:
            # This is a "FIND THE OUTFLOW" case where a B point isn't specified
            self.toEdges = self._getTerminalEdges(self.fromEdge.edge[1])

        # Now just get a list of all possible paths for all possible outflows
        for outEdge in self.toEdges:
            # Make a depth-first tree from the first headwater we find
            self._findSimplePaths(self.fromEdge, outEdge)

        # TODO: JUST RETURN THE FIRST OUTFLOW POINT IS WRONG. NEED TO ACCOMODATE MULTIPLES

        # No paths. try a reversal
        if len(self.paths) == 0:
            newProfile = copy.copy(self)
            try:
                newProfile.pathfinder(outID, inID)
                if len(newProfile.paths) > 0:
                    self.reversible = True
            except Exception, e:
                pass


    def _prepareEdges(self, rawedges):
        """
        Helper function to marry fids with NetworkX edges
        :param rawedges: edge tuple we want to augment
        :return:
        """
        return [EdgeObj(edge, self.G.get_edge_data(*edge).keys()) for edge in rawedges]

    def _getTerminalEdges(self, startPt):
        """
        Do a DFS on a tree and return all edges that are considered terminal (no downstream neighbours)
        :param startPt:
        :return:
        """
        edges = list(nx.dfs_edges(self.G, startPt))
        edges = self._prepareEdges(edges)

        return [edge for edge in edges if len(self.G.neighbors(edge.edge[1])) == 0]


    def _findSimplePaths(self, startEdge, endEdge):
        """
        Abstraction for nx.all_simple_paths
        :param startEdge:
        :param endEdge:
        :return:
        """

        # Get all possible paths
        paths = [path for path in nx.all_simple_paths(self.G, source=startEdge.edge[1], target=endEdge.edge[1])]
        # Remove duplicate traversal paths (we need to recalc them later recursively)
        nodupespaths = [x for i, x in enumerate(paths) if i == paths.index(x)]

        # Zip up the edge pairs and add the FIDs back
        pathedges = [self._prepareEdges(zip(path, path[1:])) for path in nodupespaths]

        # There may be multiple paths so we need to find indices
        for edges in pathedges:
            self._recursivePathsFinder(edges, [EdgeObj(startEdge.edge, startEdge.fids)])


    def _qgsLayertoNX(self, shapelayer, simplify=True, geom_attrs=True):
        """
        THIS IS a re-purposed version of load_shp from nx
        :param shapelayer:
        :param simplify:
        :param geom_attrs:
        :return:
        """
        self.logInfo("parsing shapefile into network...")

        self.G = nx.MultiDiGraph()
        self.logInfo("Shapefile successfully parsed into directed network")

        for f in shapelayer.getFeatures():

            flddata = f.attributes()
            fields = [str(fi.name()) for fi in f.fields()]

            geo = f.geometry()
            # We don't care about M or Z
            geo.geometry().dropMValue()
            geo.geometry().dropZValue()

            attributes = dict(zip(fields, flddata))
            # We add the _FID_ manually
            fid = int(f.id())
            attributes[self.idField] = fid
            attributes['_calc_length_'] = geo.length()

            # Note:  Using layer level geometry type
            if geo.wkbType() in (QgsWKBTypes.LineString, QgsWKBTypes.MultiLineString):
                for edge in self.edges_from_line(geo, attributes, simplify, geom_attrs):
                    e1, e2, attr = edge
                    self.features[fid] = attr
                    self.G.add_edge(e1, e2, key=attr[self.idField])
                self.cols = self.features[self.features.keys()[0]].keys()
            else:
                raise ImportError("GeometryType {} not supported. For now we only support LineString types.".
                                  format(QgsWKBTypes.displayString(int(geo.wkbType()))))


    def _recursivePathsFinder(self, edges, path=None):
        """
        Help us find all the different paths with a given combination of nodes
        :return:
        """
        newpath = path[:] if path is not None else []

        def getNext(eobjs, lastedge):
            return [EdgeObj(eobj[0], [fid]) for eobj in eobjs for fid in eobj.fids if eobj.edge[0] == lastedge.edge[1]]

        # A branch could be a real node branch or a duplicate edge
        nextEdges = getNext(edges, newpath[-1])

        # Continue along a straight edge as far as we can until we end or find a fork
        while len(nextEdges) == 1:
            newpath.append(nextEdges[0])
            # A branch could be a real node branch or a duplicate edge (same as above)
            nextEdges = getNext(edges, newpath[-1])

        if len(nextEdges) == 0:
            self.pathmsgs.append("Path found: {}. Path Length: {}".format(self.getPathEdgeIds(newpath), self._pathLength(newpath)))
            self.paths.append(newpath)
        else:
            chosenedges = self._chooseEdges(nextEdges)
            # Here is the end or a fork
            for edge in chosenedges:
                self._recursivePathsFinder(edges, newpath + [edge])

    def edges_from_line(self, geom, attrs, simplify=True, geom_attrs=True):
        """
        This is repurposed from the shape helper here:
        https://github.com/networkx/networkx/blob/master/networkx/readwrite/nx_shp.py
        :return:
        """
        if geom.wkbType() == QgsWKBTypes.LineString:
            pline = geom.asPolyline()
            if simplify:
                edge_attrs = attrs.copy()
                # DEBUGGING
                edge_attrs["Wkt"] = geom.exportToWkt()
                if geom_attrs:
                    edge_attrs["Wkb"] = geom.asWkb()
                    edge_attrs["Wkt"] = geom.exportToWkt()
                    edge_attrs["Json"] = geom.exportToGeoJSON()
                yield (pline[0], pline[-1], edge_attrs)
            else:
                for i in range(0, len(pline) - 1):
                    pt1 = pline[i]
                    pt2 = pline[i + 1]
                    edge_attrs = attrs.copy()
                    if geom_attrs:
                        segment = ogr.Geometry(ogr.wkbLineString)
                        segment.AddPoint_2D(pt1[0], pt1[1])
                        segment.AddPoint_2D(pt2[0], pt2[1])
                        edge_attrs["Wkb"] = segment.asWkb()
                        edge_attrs["Wkt"] = segment.exportToWkt()
                        edge_attrs["Json"] = segment.exportToGeoJSON()
                        del segment
                    yield (pt1, pt2, edge_attrs)

        # TODO: MULTILINESTRING MIGHT NOT WORK
        elif geom.wkbType() == QgsWKBTypes.MultiLineString:
            for i in range(geom.GetGeometryCount()):
                geom_i = geom.GetGeometryRef(i)
                for edge in self.edges_from_line(geom_i, attrs, simplify, geom_attrs):
                    yield edge


    def findEdgewithID(self, id):
        """
        One line helper function to find an edge with a given ID
        because the graph is a multiDiGraph there may be multiple edges for
        each node pair so we need to return an index to which one we mean too
        :param id:
        :return: ((edgetuple), edgeindex, attr)
        """
        # [self.G.get_edge_data(*np) for np in self.G.edges_iter()]
        foundEdge = None
        for np in self.G.edges_iter():
            keys = self.G.get_edge_data(*np).keys()
            if id in keys:
                # EdgeObj = namedtuple('EdgeObj', ['EdgeTuple', 'fid'], verbose=True)
                foundEdge = EdgeObj(np, [id])
                break

            if foundEdge is not None:
                break

        return foundEdge

    def logInfo(self, msg):
        if self.msgcallback:
            self.msgcallback(msg, color="green")
        self.metalogs.append(msg)
        self.logger.info(msg)

    def logError(self, msg):
        if self.msgcallback:
            self.msgcallback(msg, color="red")
        self.metalogs.append("[ERROR]" + msg)
        self.logger.error(msg)


    def generateCSV(self, cols=None):
        """
        Separate out the writer so we can test without writing files
        :param outdict:
        :param csv:
        :return:
        """
        self.metalogs.append("{} possible paths found based on ruleset. Choosing the shortest of these.".format(len(self.paths)))

        chosenpath = self._choosebylength()
        # Now we have to chose just one path out of the ones we have
        calcfields = self.calcfields(chosenpath)

        self.results = []
        self.logInfo("Writing CSV file")

        # Make a subset dictionary
        includedShpCols = []
        if len(cols) > 0:
            for col in cols:
                if col not in self.cols:
                    self.log
                    self.logError("WARNING: Could not find column '{}' in shapefile".format(col))
                else:
                    includedShpCols.append(col)
        else:
            includedShpCols = self.cols

        # Now just pull out the columns we need
        for node in chosenpath:
            fid = node.fids[0]
            csvDict = {}

            # The ID field is not optional
            csvDict[self.idField] = fid

            csvDict["Wkt"] = self.features[fid]['Wkt']

            # Only some of the fields get included
            for key in self.cols:
                if key in includedShpCols:
                    csvDict[key] = self.features[fid][key]

            # Everything calculated gets included
            for key, val in calcfields[fid].iteritems():
                csvDict[key] = val

            self.results.append(csvDict)

        self.csvkeys = self.results[0].keys()
        self.csvkeys.sort(self._keycolSort)


    def _chooseEdges(self, choicearr):
        """
        Choose one of the paths based on a set of rules
        :param choicearr: list of EdgeObjs we are choosing from
        :return:
        """

        chosenarr = []

        if self.choice == Profile.CHOICE_FIELD_VALUE:
            chosenarr = filter(lambda ed: self.fieldname in self.features[ed.fids[0]] and self.features[ed.fids[0]][self.fieldname] == self.fieldval, choicearr)

        elif self.choice == Profile.CHOICE_FIELD_NOT_VALUE:
            chosenarr = filter(lambda ed: self.fieldname in self.features[ed.fids[0]] and self.features[ed.fids[0]][self.fieldname] != self.fieldval, choicearr)

        elif self.choice == Profile.CHOICE_FIELD_NOT_EMPTY:
            chosenarr = filter(lambda ed: self.fieldname in self.features[ed.fids[0]] and self.features[ed.fids[0]][self.fieldname] != None and self.features[ed.fids[0]][self.fieldname] != "", choicearr)

        # If we couldn't make a decision just return everything
        if len(chosenarr) == 0:
            return choicearr
        else:
            return chosenarr

    # pyt the keys in order
    def _keycolSort(self, a, b):
        # idfield should bubble up
        if a == self.idField:
            return -1
        elif b == self.idField:
            return 1
        # put shpfields ahead of calc fields
        elif (a in self.cols and b in self.calccols):
            return -1
        elif (a in self.calccols and b in self.cols):
            return 1
        # Sort everything else alphabetically
        elif (a in self.cols and b in self.cols) or (a in self.calccols and b in self.calccols):
            if a.lower() > b.lower():
                return 1
            elif a.lower() < b.lower():
                return -1
            else:
                return 0
        else:
            return -1

    def _choosebylength(self):
        """
        We use this method to choose the shortest of a set of valid paths if there is more than one
        :param features:
        :param paths:
        :return:
        """

        if len(self.paths) == 1:
            return self.paths[0]
        # Return the top item (shortest) when sorting by length
        return sorted(self.paths, key=self._pathLength)[0]

    def _segLength(self, fid):
        return self.features[fid]['_calc_length_']

    def _pathLength(self, pathArr):
        return sum([self._segLength(x.fids[0]) for x in pathArr])