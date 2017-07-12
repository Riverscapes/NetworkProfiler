from matplotlib import pyplot as plt

class Plots():

    def __init__(self, csvpath, outputdir):
        # Open CSV file

        # Load everything into a dictionary of lists
        self.data = {}

        # Loop over legitimate columns and save PNG files to the hard disk



    def createPlots(self, csvpath, outputdir):
        for col in self.data.iteritems():
            self.plotit(col)


    def plotit(self, colname):
        print "hello"