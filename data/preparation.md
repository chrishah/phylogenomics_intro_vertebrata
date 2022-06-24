These steps were run in preparation for this repository.

```
#run setup
./phylociraptor setup -t serial=2 --config-file data/config.vertebrata_minimal.yaml --verbose

#reduce busco set to only 20 busco genes
./modify_busco.sh

#orthology
./phylociraptor orthology -t serial=2 --config-file data/config.vertebrata_minimal.yaml --verbose

#cleanup (just to save some space on Github)
rm -rf $(find ./results/orthology/busco/busco_runs/ -name "softw*")
rm ./results/orthology/busco/busco_runs/Latimeria_chalumnae/run_busco/hmmer_output.tar.gz
rm results/orthology/busco/busco_runs/Latimeria_chalumnae/run_busco/augustus_output.tar.gz
rm results/orthology/busco/busco_runs/Latimeria_chalumnae/run_busco/blast_output.tar.gz
```
