---
title: Home
weight: 1
---

The Riverscapes Analysis Viewer and Explorer (RAVE) is a [QGIS](http://www.qgis.org/en/site/) plugin you can use to interact with riverscapes data.

Using this tool you can:

* Browse the riverscapes data repository
* Download and upload riverscapes projects
* View riverscapes project data using the QGIS map viewer.

### Getting Started: 

1. [Quick Start Guide](quickstart.html)
2. [Anatomy of the plugin](anatomy.html)

### Development

The RAVE plugin is under active development by [North Arrow Research](http://northarrowresearch.com) with contributions from [South Fork Research](http://southforkresearch.org) and the [Fluvial Habitats](http://fluvialhabitats.org) at Utah State University. Funding for these tools was provided by the Bonneville Power Administration (BPA Proposal # 2011-006-00 & BPA Project: 2003-017-00) and NOAA as part of the [Columbia Habitat Monitoring Program](http://www.champmonitoring.org/) (CHaMP).

RAVE is scalable and intended to accommodate additional riverscapes projects over time. Model owners are encouraged to contact North Arrow Research if they want to integrate their model into the riverscapes framework. There are currently two things that model owners can contribute to the riverscapes project to help their projects be visible and usable within the RAVE plugin:

* **[Symbolizing layers](Development/symbolizers.html)**: Create symbolizers so that layers of a certain type are always symbolized the same way when layers are added to the QGIS map window. There are mechanisms for both Raster and Vector symbolization.
* **[Project Parsers](Development/businesslogic.html)**: This is a single XML file that determines how each project type gets parsed by the QGIS layer manager. Essentially it tells RAVE how to add project layers to the QGIS table of contents.

### License

Licensed under the [GNU General Public License Version 3](https://github.com/Riverscapes/RiverscapesToolbar/blob/master/LICENSE).