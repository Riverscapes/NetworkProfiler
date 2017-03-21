# Network Profiler QGIS Plugin

This is a QGis python plugin that is designed to profile a particular stream network from a start point to an end point and output a CSV file.

## Requirements

You must have QGis installed. This plugin also requires `networkx`. Most QGis users should already have networkx installed but if you don't then you need to go get it:

``` bash
pip install networkx
```


## Installation

Until this plugin is available on the plugin store you're going to need to install it manually.

1. Make sure QGis is closed.
2. Download this repo and unzip it into: `c:\Users\<USERNAME>\.qgis2\python\plugins\network-profiler\`. If you see the file: `c:\Users\<USERNAME>\.qgis2\python\plugins\network-profiler\README.md` you've done it right.
3. Reload QGis and go to the plugins menu. You should be able to check the box next to network profiler.
