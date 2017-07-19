from PyQt4.QtGui import QColor
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsSymbolV2, QgsSingleSymbolRendererV2, QgsSimpleLineSymbolLayerV2


def addToMap(csvfile, selectedLayer):

    uri = "file://{0}?delimiter={1}&crs={2}&wktField={3}".format(csvfile,",", selectedLayer.crs().authid(), "Wkt")
    rOutput = QgsVectorLayer(uri, "ProfileLayer_{}".format(selectedLayer.name()), "delimitedtext")

    symbolize(rOutput, selectedLayer)
    QgsMapLayerRegistry.instance().addMapLayer(rOutput)

    print "hello"

def symbolize(layer, oldlayer):
    provider = layer.dataProvider()
    extent = layer.extent()
    renderer = None

    # See if we can figure out ho thick the line is to begin with:

    # create a new single symbol renderer
    symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
    renderer = QgsSingleSymbolRendererV2(symbol)

    # symbol_layer = QgsSimpleLineSymbolLayerV2.create(properties)
    symbol_layer = QgsSimpleLineSymbolLayerV2(QColor('red'), 2.0)
    # assign the symbol layer to the symbol
    renderer.symbol().appendSymbolLayer(symbol_layer)
    # assign the renderer to the layer
    layer.setRendererV2(renderer)


