from logger import Logger
from shapefiles import Shapefile
import csv
import networkx as nx

class Profile():

    def __init__(self, shpfile, idField, inID, outID=None):
        """
        Profile a network from startID to endID

        If no outID is specified we go and found the outflow point and use that

        :param shpfile: The Shape file to open
        :param inID:  The ID of the input network segment
        :param outID:  The ID of the output network segment (Optional) Default is none
        """
        # TODO: Could not find because those points are in two different subnetworks. Please fix your network
        # TODO: Could not find because stream flow was a problem. If you reverse your input and output then it works

        log = Logger("Main")

        # We need to open the shapefile first:
        log.info("Opening shapefile...")
        self.network = Shapefile(shpfile)
        self.idfield = self.network.getIDField()
        # Parse the network
        try:
            log.info("parsing shapefile into network...")
            G = nx.read_shp(shpfile, simplify=True)
            log.info("Shapefile successfully parsed into directed network")
        except Exception as e:
            log.error("Error parsing network", e)
        log = Logger("Main")

        startNode = self.findnodewithID(G, inID, self.idfield)

        if not startNode:
            raise Exception("Could not find start ID: {} in network.".format(inID))

        if outID:
            endNode = self.findnodewithID(G, outID, self.idfield)
            if not endNode:
                raise Exception("Could not find end ID: {} in network.".format(outID))
            # Make a depth-first tree from the first headwater we find
            try:
                shortestpath = nx.shortest_path(G, source=startNode[0], target=endNode[1])
                self.path_edges = zip(shortestpath, shortestpath[1:])
            except Exception, e:
                log.error("Path not found between these two points with id: '{}' and '{}'".format(inID, outID))
                raise e
        else:
            try:
                self.path_edges = list(nx.dfs_edges(G, startNode[0]))
            except Exception, e:
                log.error("Path not found between input point with ID: {} and outflow point".format(inID))


        self.attr = []
        log.info('Calculating lengths...')
        cummulativelength = 0
        for edge in self.path_edges:
            # Get the ID for this edge
            shapeID = G.get_edge_data(*edge)[self.idfield]

            # We do this later so that we don't have to convert every shape.
            shapelyObj = self.network.featureToShapely(shapeID)

            # NetworkX stores the fields in attribute tables but we retrieve them from the shapefile directly
            # to remain consistent
            attrField = shapelyObj['fields']

            attrCalc = {}
            attrCalc['ProfileCalculatedLength'] = shapelyObj['geometry'].length
            cummulativelength += attrCalc['ProfileCalculatedLength']
            attrCalc['ProfileCummulativeLength'] = cummulativelength

            # Calculate length and cumulative length
            self.attr.append({
                'shpfields': attrField,
                'calculated': attrCalc
            })
        log.info('Pathfinding complete. Found a path with {} segments'.format(len(self.attr)))


    def findnodewithID(self, G, id, idField):
        """
        One line helper function to find a node with a given ID
        :param id:
        :return:
        """
        Logger("FindWithID")
        for e in G.edges_iter():
            data = G.get_edge_data(*e)
        return next(iter([e for e in G.edges_iter() if G.get_edge_data(*e)[idField] == id]), None)


    def writeCSV(self, filename, colstr = ""):
        """
        Separate out the writer so we can test without writing files
        :param outdict:
        :param csv:
        :return:
        """
        log = Logger("CSV Writer")
        results = []
        log.info("Writing CSV file")
        if len(self.attr) == 0:
            log.error("WARNING: No rows to write to CSV. Nothing done")
            return

        # Make a subset dictionary
        includedShpCols = []
        if len(colstr) > 0:
            inputDesiredCols = colstr.split(',')
            for col in inputDesiredCols:
                if col not in results[0]:
                    log.error("WARNING: Could not find column '{}' in shapefile".format(col))
                else:
                    includedShpCols.append(col)
        else:
            includedShpCols = self.attr[0]['shpfields'].keys()

        # Now just pull out the columns we need
        for node in self.attr:
            csvDict = {}

            # The ID field is not optional
            csvDict[self.idfield] = node['shpfields'][self.idfield]

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
                if a == self.idfield:
                    return -1
                if b == self.idfield:
                    return 1
                # put shpfields ahead of calc fields
                if (a in item['shpfields'] and b in item['calculated']):
                    return -1
                if (a in item['calculated'] and b in item['shpfields']):
                    return 1
                # Sort everything else alphabetically
                if (a in item['shpfields'] and b in item['shpfields']) or (a in item['calculated'] and b in item['calculated']):
                    if a.lower() > b.lower():
                        return 1
                    elif a.lower() < b.lower():
                        return -1
                    else:
                        return 0

            keys.sort(colSort)


            writer = csv.DictWriter(filename, keys)
            writer.writeheader()
            writer.writerows(results)