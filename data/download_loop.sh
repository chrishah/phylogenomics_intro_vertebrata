#!/bin/bash

for line in $(cat data/samples.exercise.csv)
do
	species=$(echo "$line" | cut -d "," -f 1)
	url=$(echo "$line" | cut -d "," -f 2)
	echo -e "\ndownloading $species from $url"
	mkdir -p assemblies/$species
	cd assemblies/$species
	wget $url
	cd -
done
