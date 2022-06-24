#!/bin/bash


echo "This script modifies the downloaded busco set so that it only includes 10 genes for use with the minimal test_case."

buscotmp="busco_tmp/vertebrata_odb10"
buscodir="results/orthology/busco/busco_set/vertebrata_odb10"
buscos="320238at7742 228730at7742 164538at7742 97645at7742 42971at7742 193525at7742 332227at7742 403632at7742 378120at7742 353318at7742 33940at7742 342641at7742 359032at7742 361842at7742 378120at7742 404316at7742 406935at7742 409625at7742 409719at7742 413149at7742"


rm -rf $buscotmp

mkdir -p $buscotmp $buscotmp/info $buscotmp/hmms $buscotmp/prfl


if [[ ! -d $buscodir ]]; 
then
	echo "Directory $buscodir not found. Did you run phylociraptor setup and is this script in the phylociraptor base directory?"
	exit 1
fi

echo "Copy hmms and prfl files"

for gene in $buscos; do
	cp $buscodir/hmms/$gene.hmm $buscotmp/hmms
	cp $buscodir/prfl/$gene.prfl $buscotmp/prfl
done

echo "Reducing files in info directory"
#info=$(basename $(find $buscodir/info/ -name "*_orthogroup_info.txt.gz"))
#zcat $buscodir/info/$info | head -n 1 > $buscotmp/info/$(echo "$info" | sed 's/.gz$//')
#for gene in $buscos; do
#	zcat $buscodir/info/$info | grep $gene
#done >> $buscotmp/info/*_orthogroup_info.txt
#gzip $buscotmp/info/*_orthogroup_info.txt

for gene in $buscos; do
	cat $buscodir/info/ogs.id.info | grep $gene
done > $buscotmp/info/ogs.id.info 

cp $buscodir/info/species.info $buscotmp/info
if [[ -f $buscodir/info/changelog ]]; then cp $buscodir/info/changelog $buscotmp/info/; fi

echo "Reducing lengths and score cutoff files"

for gene in $buscos; do
	cat $buscodir/lengths_cutoff | grep $gene
done > $buscotmp/lengths_cutoff

for gene in $buscos; do
	cat $buscodir/scores_cutoff | grep $gene
done > $buscotmp/scores_cutoff

echo "Copy ancestral files"

cp $buscodir/ancestral $buscotmp/
cp $buscodir/ancestral_variants $buscotmp/

echo "Modify dataset.cfg"

cat $buscodir/dataset.cfg | sed -e "s/number_of_BUSCOs=.*/number_of_BUSCOs=$(for i in $buscos; do echo $i; done | wc -l)/" > $buscotmp/dataset.cfg

echo "Replace busco directory with modified version"
echo "A Backup of the original busco directory will be kept in results/orthology/busco/busco_set_backup"

mv $buscodir results/orthology/busco/busco_set_backup
mv $buscotmp $buscodir

echo "done"
