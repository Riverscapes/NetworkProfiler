---
title: Home
weight: 1
---

This is a [QGIS](git@github.com:Riverscapes/NetworkProfiler.git) python plugin that traverses a polyline network from a start point to an end point and output the feature attributes to CSV from the features along the path through the network.

### Requirements

You must have [QGIS](git@github.com:Riverscapes/NetworkProfiler.git) installed. This plugin also requires [NetworkX](https://networkx.github.io/documentation/stable/index.html). Most QGIS users should already have NetworkX installed but if you don't then you need to go get it either through your QGIS plugins dialog or using the following command:

``` bash
pip install networkx
```

### Plugin Installation

Until this plugin is available on the plugin store you're going to need to install it manually:

1. Make sure QGIS is closed.
2. Download this repo and unzip it into: `c:\Users\<USERNAME>\.qgis2\python\plugins\NetworkProfiler\`. If you see the file: `c:\Users\<USERNAME>\.qgis2\python\plugins\NetworkProfiler\README.md` you've done it right.
3. Start QGIS and go to the plugins menu. You should be able to check the box next to network profiler.

### Steps to use the Profiler

1. Open up the Network Profiler tool.
2. You can either select a layer from the dropdown or use the grab button and the layer will be selected for you.
3. Using the "QGIS feature select tool" (Button: yellow square with marching ants and a white cursor) to select a single feature in the network that you want to use as your start point.
4. Click the "Grab From Map Selection" button and you should see the field values get populated below.
5. Select the fields you want to include in your CSV file. You should also select some kind of ID field (OBJECTID or FID) if you want to be able to identify your features afterwards.
6. Enter a path to the CSV file.
6. Click the "Create Profile" button to continue. After 4-5 seconds you should get a success message.

### If You Get Errors

Please click the "more info" button and then [log an issue in the GitHub repo](https://github.com/Riverscapes/NetworkProfiler/issues). Attach yuor ShapeFiles if they are not too big.

### Deploy

1. `pb_tool zip`
2. rename the zip to `NetworkProfiler-0.0.1.zip` CAREFUL OF VERSION
3. upload it

```
aws s3 cp NetworkProfiler-0.0.1.zip s3://qgis.northarrowresearch.com/plugins/networkprofiler/
```

Now update the `Plugins.xml` wherever this is being served. Be sure to update the Version.