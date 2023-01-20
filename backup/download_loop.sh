#!/bin/bash

for f in $(cat data/samples.csv | tail -n 2)
do
	name=$(echo $f | cut -d "," -f 1)
	url=$(echo $f | cut -d "," -f 2)
	mkdir -p assemblies/${name}
	wget $url -P assemblies/${name}/
done
