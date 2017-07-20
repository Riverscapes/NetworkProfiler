from PyQt4.QtGui import QColor
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsSymbolV2, QgsSingleSymbolRendererV2, QgsSimpleLineSymbolLayerV2
import random
import colorsys
from qgis.utils import iface


def addToMap(csvfile, selectedLayer):
    # A little windows path trickery
    if csvfile[0] is not "/":
        csvfile = "/" + csvfile

    uri = "file://{0}?delimiter={1}&crs={2}&wktField={3}".format(csvfile,",", selectedLayer.crs().authid(), "Wkt")
    rOutput = QgsVectorLayer(uri, "ProfileLayer_{}".format(selectedLayer.name()), "delimitedtext")

    symbolize(rOutput, selectedLayer)
    QgsMapLayerRegistry.instance().addMapLayer(rOutput)

    # Make sure this doesn't change the active layer selection
    iface.setActiveLayer(selectedLayer)



def random_color():
    h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
    r, g, b = [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]
    return QColor(r,g,b,150)

def symbolize(layer, oldlayer):
    renderer = None

    # See if we can figure out ho thick the line is to begin with:
    # create a new single symbol renderer
    symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
    renderer = QgsSingleSymbolRendererV2(symbol)

    # symbol_layer = QgsSimpleLineSymbolLayerV2.create(properties)
    symbol_layer = QgsSimpleLineSymbolLayerV2(random_color(), 2.0)

    # assign the symbol layer to the symbol
    # TODO: on windows:::  'NoneType' object has no attribute 'appendSymbolLayer'
    renderer.symbol().appendSymbolLayer(symbol_layer)

    # assign the renderer to the layer
    layer.setRendererV2(renderer)


