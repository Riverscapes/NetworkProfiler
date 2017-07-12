import csv
import networkx as nx
import ogr
from qgis.core import *
import logging
from collections import namedtuple
from shapely import wkb

"""
We invented a special kind of tuple to handle all the different properties of an "Edge"
"""
EdgeObj = namedtuple('EdgeObj', ['edge', 'fid'])


class Profile():

    CHOICE_SHORTEST = "Shortest Path Length"
    CHOICE_FIELD_NOT_EMPTY = "Field not empty"
    CHOICE_FIELD_VALUE = "Field has value"
    CHOICE_FIELD_NOT_VALUE = "Field does not have value"

    def __init__(self, shpLayer, choice=None, fieldname=None, fieldval=None, msgcallback=None):
        """
        Profile a network from startID to endID

        If no outID is specified we go and found the outflow point and use that
        """

        self.logger = logging.getLogger('Profile')
        self.msgcallback = msgcallback

        self.idField = "_FID_"
        self.metalogs = []
        self.pathmsgs = []

        self.paths = []

        self.features = {}

        # Convert QgsLayer to NX graph
        self._qgsLayertoNX(shpLayer, simplify=True)

        self.choice = Profile.CHOICE_SHORTEST if choice is None else choice

        self.fieldname = fieldname
        self.fieldval = fieldval

        if fieldname is None and choice == Profile.CHOICE_FIELD_VALUE or choice == Profile.CHOICE_FIELD_NOT_EMPTY:
            raise Exception("ERROR: If you want to use a field option you need to specify a field")

        if fieldval is None and choice == Profile.CHOICE_FIELD_VALUE:
            raise Exception("ERROR: If you your path choice involves a field value you must provide one")

    def getPathEdgeIds(self, path=None):
        """
        Get the FIDs of all the paths in the object
        :return:
        """
        ids = []

        if path is None:
            for p in self.paths:
                ids.append([idx[1] for idx in p])
        else:
            ids = [idx[1] for idx in path]

        return ids

    def _calcfields(self, edges):
        """
        These are fields that need to be calculated.
        :param edges:
        :return:
        """
        path = []

        cummulativelength = 0
        for idx, edge in enumerate(edges):
            # Get the ID for this edge
            attrFields ={}
            attrCalc = {}
            attrFields = { k: v for k, v in self.G.get_edge_data(*edge).iteritems() if k.lower() not in ['json', 'wkb', 'wkt'] }

            attrCalc = {}
            attrCalc['ProfileCalculatedLength'] = attrFields['_calc_length_']
            cummulativelength += attrCalc['ProfileCalculatedLength']
            attrCalc['ProfileCummulativeLength'] = cummulativelength
            attrCalc['ProfileID'] = idx + 1
            # Calculate length and cumulative length
            # EdgeObj = namedtuple('EdgeObj', ['EdgeTuple', 'KIndex', 'Attr', 'CalcAttr'], verbose=True)
            path.append(EdgeObj(edge, attrFields, attrCalc))

        return path


    def pathfinder(self, inID, outID=None):
        """
        Find the shortest path between two nodes or just one node and the outflow
        :param G:
        :param inID:
        :param outID:
        :return:
        """
        self.paths = []

        startEdge = self.findEdgewithID(inID)

        if not startEdge:
            raise Exception("Could not find start ID: {} in network.".format(inID))

        if outID:
            endEdge = self.findEdgewithID(outID)
            if not endEdge:
                raise Exception("Could not find end ID: {} in network.".format(outID))

            # Make a depth-first tree from the first headwater we find
            try:
                self._findSimplePaths(startEdge, endEdge)
            except Exception, e:
                raise Exception("Path not found between these two points with id: '{}' and '{}'".format(inID, outID))
        else:
            # This is a "FIND THE OUTFLOW" case where a B point isn't specified
            try:
                outflowEdges = self._getTerminalEdges(startEdge.edge[1])

                # Now just get a list of all the outflow points
                for outEdge in outflowEdges:
                    self._findSimplePaths(startEdge, outEdge)

            except Exception, e:
                raise Exception("Path not found between input point with ID: {} and outflow point".format(inID))

        # We're not always guaranteed to have both input and output points.
        # Returning them helps us.
        return (inID, outID)

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
            self._recursivePathsFinder(edges, [EdgeObj(startEdge.edge, startEdge.fid)])


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
            else:
                raise ImportError("GeometryType {} not supported. For now we only support LineString types.".
                                  format(QgsWKBTypes.displayString(int(geo.wkbType()))))


    def _recursivePathsFinder(self, edges, path=[]):
        """
        Help us find all the different paths with a given combination of nodes
        :return:
        """
        newpath = path[:]

        def getNext(eobjs, lastedge):
            return [EdgeObj(eobj[0], fid) for eobj in eobjs for fid in eobj.fid if eobj.edge[0] == lastedge.edge[1]]

        # A branch could be a real node branch or a duplicate edge
        nextEdges = getNext(edges, newpath[-1])

        # Continue along a straight edge as far as we can until we end or find a fork
        while len(nextEdges) == 1:
            newpath.append(nextEdges[0])
            # A branch could be a real node branch or a duplicate edge (same as above)
            nextEdges = getNext(edges, newpath[-1])

        if len(nextEdges) == 0:
            self.paths.append(newpath)
        else:
            chosenedges = self._chooseEdges(nextEdges)
            # Here is the end or a fork
            for edge in nextEdges:
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
            for k in self.G.get_edge_data(*np).iterkeys():
                if k == id:
                    # EdgeObj = namedtuple('EdgeObj', ['EdgeTuple', 'fid'], verbose=True)
                    foundEdge = EdgeObj(np, k)
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
        self.logmsgs.append("[ERROR]" + msg)
        self.logger.error(msg)


    def writeCSV(self, filename, cols=None):
        """
        Separate out the writer so we can test without writing files
        :param outdict:
        :param csv:
        :return:
        """
        chosenpath = self.pathchoice.choosebylength(self.features, self.paths)
        # Now we have to chose just one path out of the ones we have

        results = []
        self.logInfo("Writing CSV file")
        if len(self.attr) == 0:
            self.logError("WARNING: No rows to write to CSV. Nothing done")
            return

        # Make a subset dictionary
        includedShpCols = []
        if len(cols) > 0:
            for col in cols:
                if col not in self.attr[0]['shpfields']:
                    self.logError("WARNING: Could not find column '{}' in shapefile".format(col))
                else:
                    includedShpCols.append(col)
        else:
            includedShpCols = self.attr[0]['shpfields'].keys()

        # Now just pull out the columns we need
        for node in self.attr:
            csvDict = {}

            # The ID field is not optional
            # TODO: Hardcoding "FID" might not be the best idea here
            csvDict[self.idField] = node['shpfields'][self.idField]

            # Debug gets the Wkt
            # if self.debug:
            csvDict["Wkt"] = node['shpfields']['Wkt']

            # Only some of the fields get included
            for key, val in node['shpfields'].iteritems():
                if key in includedShpCols:
                    csvDict[key] = val
            # Everything calculated gets included
            for key, val in node['calculated'].iteritems():
                csvDict[key] = val

            results.append(csvDict)


        with open(filename, 'wb') as filename:
            keys = results[0].keys()

            # pyt the keys in order
            def colSort(a, b):
                # idfield should bubble up
                item = self.attr[0]
                if a == self.idField:
                    return -1
                elif b == self.idField:
                    return 1
                # put shpfields ahead of calc fields
                elif (a in item['shpfields'] and b in item['calculated']):
                    return -1
                elif (a in item['calculated'] and b in item['shpfields']):
                    return 1
                # Sort everything else alphabetically
                elif (a in item['shpfields'] and b in item['shpfields']) or (a in item['calculated'] and b in item['calculated']):
                    if a.lower() > b.lower():
                        return 1
                    elif a.lower() < b.lower():
                        return -1
                    else:
                        return 0
                else:
                    return -1

            keys.sort(colSort)

            writer = csv.DictWriter(filename, keys)
            writer.writeheader()
            writer.writerows(results)
        self.logInfo("Done Writing CSV")

    def _chooseEdges(self, choicearr):
        """
        Choose one of the paths based on a set of rules
        :param choicearr: list of EdgeObjs we are choosing from
        :return:
        """

        chosenarr = []

        if self.choice == Profile.CHOICE_FIELD_VALUE:
            chosenarr = filter(lambda ed: self.fieldname in self.features[ed.fid] and self.features[ed.fid][self.fieldname] == self.fieldval, choicearr)

        elif self.choice == Profile.CHOICE_FIELD_NOT_VALUE:
            chosenarr = filter(lambda ed: self.fieldname in self.features[ed.fid] and self.features[ed.fid][self.fieldname] != self.fieldval, choicearr)

        elif self.choice == Profile.CHOICE_FIELD_NOT_EMPTY:
            chosenarr = filter(lambda ed: self.fieldname in self.features[ed.fid] and self.features[ed.fid][self.fieldname] != None and self.features[ed.fid][self.fieldname] != "", choicearr)

        # If we couldn't make a decision just return everything
        if len(chosenarr) == 0:
            return choicearr
        else:
            return chosenarr

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
        return wkb.loads(self.features[fid]['Wkb']).length

    def _pathLength(self, pathArr):
        return sum([self._segLength(x.fid) for x in pathArr])