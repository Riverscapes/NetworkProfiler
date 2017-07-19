import matplotlib.pyplot as plt
import numbers
from os import path

class Plots():

    def __init__(self, profile, outputdir):
        # Open CSV file
        self.outputdir = outputdir
        self.profile = profile

        self.xvals = [v['ProfileCummulativeLength'] for v in self.profile.results]

    def createPlots(self):
        for col in self.profile.csvkeys:
            if col not in ['ProfileCummulativeLength', '_FID_', '']:
                filename = path.join(self.outputdir, "Plot_{}_km.png".format(col))
                self.plotit(col, filename)


    def plotit(self, colname, filename):

        yvals = [v[colname] for v in self.profile.results]

        # Only plot numeric values for now:
        if not isinstance(yvals[0], numbers.Number):
            return

        # Common sizes: (10, 7.5) and (12, 9)
        plt.figure(figsize=(12, 9))
        # Remove the plot frame lines. They are unnecessary chartjunk.

        ax = plt.subplot(111)
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

        # Ensure that the axis ticks only show up on the bottom and left of the plot.
        # Ticks on the right and top of the plot are generally unnecessary chartjunk.
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

        # Make sure your axis ticks are large enough to be easily read.
        # You don't want your viewers squinting to read your plot.
        plt.yticks(fontsize=14)
        plt.xticks(fontsize=14)

        # Provide tick lines across the plot to help your viewers trace along
        # the axis ticks. Make sure that the lines are light and small so they
        # don't obscure the primary data lines.
        plt.plot(self.xvals, yvals, "-o", lw=0.5, color="black", alpha=0.3)

            # Remove the tick marks; they are unnecessary with the tick lines we just plotted.
        plt.tick_params(axis="both", which="both", bottom="off", top="off",
                        labelbottom="on", left="off", right="off", labelleft="on")

        plt.xlabel('Cummulative Distance', fontsize=18)
        plt.ylabel(colname, fontsize=16)

        ax.autoscale_view(True,True,True)

        # # Finally, save the figure as a PNG.
        # # You can also save it as a PDF, JPEG, etc.
        # # Just change the file extension in this call.
        # # bbox_inches="tight" removes all the extra whitespace on the edges of your plot.
        plt.savefig(filename, bbox_inches="tight")