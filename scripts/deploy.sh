#!/bin/bash

NEWVERSION=$1

sed -i -- "s/^version=.*/version=${NEWVERSION}/g" metadata.txt

git checkout master
rm metadata.txt--
git add metadata.txt
git commit -m "Upgrading to version: $NEWVERSION"
git tag $NEWVERSION
git push --all

# Now make a zip and upload it
pb_tool zip
aws s3 cp NetworkProfiler.zip s3://qgis.northarrowresearch.com/plugins/networkprofiler/v$NEWVERSION/NetworkProfiler.zip
rm NetworkProfiler.zip

# Now let dev catchup
git checkout dev
git merge master
git push