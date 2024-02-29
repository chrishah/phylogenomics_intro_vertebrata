#!/bin/bash

for gene in $(echo "359032at7742 413149at7742 409719at7742 406935at7742")
do
        echo -e "\n$(date)\t$gene"
        echo -e "$(date)\taligning"
        singularity exec ~/Shared_folder/Singularity_images/clustalo_1.2.4.sif clustalo -i by_gene/raw/${gene}_all.fas -o by_gene/aligned/${gene}.clustalo.fasta --threads=2
        echo -e "$(date)\ttrimming"
        singularity exec ~/Shared_folder/Singularity_images/trimal_1.4.1.sif trimal -in by_gene/aligned/${gene}.clustalo.fasta -out by_gene/trimmed/${gene}.clustalo.trimal.fasta -gappyout

        echo -e "$(date)\ttree inference"
	mkdir -p by_gene/phylogeny/${gene}
        singularity exec ~/Shared_folder/Singularity_images/iqtree_2.0.7.sif \
              iqtree \
              -s by_gene/trimmed/${gene}.clustalo.trimal.fasta \
              --prefix by_gene/phylogeny/${gene}/${gene} \
              -m MFP --seqtype AA -T 2 -bb 1000

        echo -e "$(date)\tDone"
done
