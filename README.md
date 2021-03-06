# phylogenomics_intro_vertebrata
Phylogenomics tutorial based on BUSCO genes

***Disclaimer***
To follow the demo and make the most of it, it helps if you have some basic skills with running software tools and manipulating files using the Unix shell command line. It assumes you have Docker installed on your computer (tested with Docker version 18.09.7, build 2d0083d; on Ubuntu 18.04).

## Introduction

We will be reconstructing the phylogenetic relationships of some (iconic) vertebrates based on previously published whole genome data. The list of species we will be including in the analyses, and the URL for the data download can be found in this <a href="https://github.com/chrishah/phylogenomics_intro_vertebrata/tree/main/data/samples.csv" title="Sample table" target="_blank">table</a>.

All software used in the demo is deposited as Docker images on <a href="https://hub.docker.com/" title="Dockerhub" target="_blank">Dockerhub</a> and all data is freely and publicly available.

The workflow we will demonstrate is as follows:
- Download genomes from Genbank
- Identifying complete BUSCO genes in each of the genomes
- pre-filtering of orthology/BUSCO groups
- For each BUSCO group:
  - build alignment
  - trim alignment
  - identify model of protein evolution
  - infer phylogenetic tree (ML)
- construct supermatrix from individual gene alignments
- infer phylogenomic tree with paritions corresponding to the original gene alignments using ML
- map internode certainty (IC) onto the phylogenomic tree

### Let's begin

Before you get going I suggest you download this repository, so have all scripts that you'll need. Ideally you'd do it through `git`.
```bash
(user@host)-$ git clone https://github.com/chrishah/phylogenomics_intro_vertebrata.git
```

Then move into the newly cloned directory, and get ready.
```bash
(user@host)-$ cd phylogenomics_intro_vertebrata
```

__1.) Download data from Genbank__

What's the first species of vertebrate that pops into your head? _Latimeria chalumnae_ perhaps? Let's see if someone has already attempted to sequence its genome. 
NCBI Genbank is usually a good place to start. Surf to the [webpage](https://www.ncbi.nlm.nih.gov/genome/) and have a look. And indeed we are [lucky](https://www.ncbi.nlm.nih.gov/genome/?term=Latimeria+chalumnae).  

Let's get it downloaded. Note that the `(user@host)-$` part of the code below just mimics a command line prompt. This will look differently on each computer. The command you actually need to exectue is the part after that, so only, e.g. `mkdir assemblies`:
```bash
#First make a directory and enter it
(user@host)-$ mkdir assemblies
(user@host)-$ mkdir assemblies/Latimeria_chalumnae
(user@host)-$ cd assemblies/Latimeria_chalumnae


#use the wget program to download the genome
(user@host)-$ wget https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/225/785/GCF_000225785.1_LatCha1/GCF_000225785.1_LatCha1_genomic.fna.gz

#decompress for future use
(user@host)-$ gunzip GCF_000237925.1_ASM23792v2_genomic.fna.gz

#leave the directory for now
(user@host)-$ cd ../..
```
We have compiled a list of published genomes that we will be including in our analyses [here](https://github.com/chrishah/phylogenomics_intro_vertebrata/tree/main/data/samples.csv). You don't have to download them all now, but do another few just as practice. You can do one by one or use your scripting skills (for loop) to get them all in one go. 

To keep things clean I'd suggest to download each into a separate directory that should be named according to the binomial (connected with underscores, rather than spaces) - see example for _L. chalumnae_ above.

__2.) Run BUSCO on each assembly__

***Attention***
> Since these genomes are relatively large BUSCO takes quite a while to run so this step has been already done for you.

A reduced representation of the BUSCO results for each species ships with the repository in the directory `results/orthology/busco/busco_runs`.

Take a few minutes to explore the reports.

__3.) Prefiltering of BUSCO groups__

Now, assuming that we ran BUSCO across a number of genomes, we're going to select us a bunch of BUSCO genes to be included in our phylogenomic analyses. Let's get and overview.

We have a script to produce a matrix of presence/absence of BUSCO genes across multiple species. Let's try it out. In this tutorial we'll be using Docker containers through Singularity.

```bash
(user@host)-$ singularity exec docker://reslp/biopython_plus:1.77 \
              bin/extract_busco_table.py \
              --hmm results/orthology/busco/busco_set/vertebrata_odb10/hmms \
              --busco_results results/orthology/busco/busco_runs/ \
              -o busco_table.tsv
```

The resulting file `busco_table.tsv` can be found in your current directory.

We'd want for example to identify all genes that are present in at least 20 of our 25 taxa and concatenate the sequences from each species into a single fasta file.

```bash
(user@host)-$ mkdir -p by_gene/raw
(user@host)-$ singularity exec docker://reslp/biopython_plus:1.77 \
              bin/create_sequence_files.py \
              --busco_table busco_table.tsv \
              --busco_results results/orthology/busco/busco_runs \
              --cutoff 0.5 \
              --outdir by_gene/raw \
              --minsp 20 \
              --type aa \
              --gene_statistics gene_stats.txt \
              --genome_statistics genome_statistics.txt 
```

A bunch of files have been created in your current directory (`gene_stats.txt`) and also in the directory `by_gene/raw` (per gene `fasta` files).

__4.) For each BUSCO group__

For each of the BUSCOs that passed we want to:
 - do multiple sequence alignment
 - filter the alignment, i.e. remove ambiguous/problematic positions
 - build a phylogenetic tree

Let's go over a possible solution step by step for gene: `409625at7742`.

Perform multiple sequence alignment with [clustalo](http://www.clustal.org/omega/).
```bash
#alignment with clustalo
(user@host)-$ mkdir by_gene/aligned
(user@host)-$ singularity exec docker://reslp/clustalo:1.2.4 \
              clustalo \
              -i by_gene/raw/409625at7742_all.fas \
              -o by_gene/aligned/409625at7742.clustalo.fasta \
              --threads=2
```

We can then look at the alignment result. There is a number of programs available to do that, e.g. MEGA, Jalview, Aliview, or you can do it online. A link to the upload client for the NCBI Multiple Sequence Alignment Viewer is [here](https://www.ncbi.nlm.nih.gov/projects/msaviewer/?appname=ncbi_msav&openuploaddialog) (I suggest to open in new tab). Upload (`by_gene/aligned/409625at7742.clustalo.fasta`), press 'Close' button, and have a look.

What do you think? It's actually quite messy.. 

Let's move on to score and filter the alignment, using [TrimAl](https://vicfero.github.io/trimal/).

```bash
#alignment trimming with trimal
(user@host)-$ mkdir by_gene/trimmed
(user@host)-$ singularity exec docker://reslp/trimal:1.4.1 \
              trimal \
              -in by_gene/aligned/409625at7742.clustalo.fasta \
              -out by_gene/trimmed/409625at7742.clustalo.trimal.fasta \
              -gappyout
```

Try open the upload [dialog](https://www.ncbi.nlm.nih.gov/projects/msaviewer/?appname=ncbi_msav&openuploaddialog) for the Alignment viewer in a new tab and upload the new file (`by_gene/trimmed/409625at7742.clustalo.trimal.fasta`).
What do you think? The algorithm has removed quite a bit at the ends of the original alignment, reducing it to only ~100, but these look mostly ok, at first glance.

Now, let's infer a ML tree with [IQtree](http://www.iqtree.org/).

```bash
#ML inference with IQTree
(user@host)-$ mkdir -p by_gene/phylogeny/409625at7742
(user@host)-$ singularity exec docker://reslp/iqtree:2.0.7 \
              iqtree \
              -s by_gene/trimmed/409625at7742.clustalo.trimal.fasta \
              --prefix by_gene/phylogeny/409625at7742/409625at7742 \
              -m MFP --seqtype AA -T 2 -bb 1000
```

The best scoring Maximum Likelihood tree can be found in the file: `by_gene/phylogeny/409625at7742/409625at7742.treefile`.

The tree is in the Newick tree format. There is a bunch of programs that allow you to view and manipulate trees in this format. You can only do it online, for example through [iTOL](https://itol.embl.de/upload.cgi), embl's online tree viewer. There is others, e.g. [ETE3](http://etetoolkit.org/treeview/), [icytree](https://icytree.org/), or [trex](http://www.trex.uqam.ca/index.php?action=newick&project=trex). You can try it out, but first let's have a quick look at the terminal.

```bash
(user@host)-$ cat by_gene/phylogeny/409625at7742/409625at7742.treefile
```

__Well done!__


__5.) Run the process for multiple genes__

Now, let's say we want to go over these steps for multiple genes, say these:
 - 359032at7742
 - 413149at7742 
 - 409719at7742
 - 406935at7742

For loop would do the job right? See the below code. Do you manage to add the tree inference step in, too? It's not in there yet.
```bash
(user@host)-$ for gene in $(echo "359032at7742 413149at7742 409719at7742 406935at7742")
do
        echo -e "\n$(date)\t$gene"
        echo -e "$(date)\taligning"
        singularity exec docker://reslp/clustalo:1.2.4 clustalo -i by_gene/raw/${gene}_all.fas -o by_gene/aligned/${gene}.clustalo.fasta --threads=2
        echo -e "$(date)\ttrimming"
        singularity exec docker://reslp/trimal:1.4.1 trimal -in by_gene/aligned/${gene}.clustalo.fasta -out by_gene/trimmed/${gene}.clustalo.trimal.fasta -gappyout
        echo -e "$(date)\tDone"
done
```

Now, let's infer an ML tree using a supermatrix of all 5 genes that we have processed so far.
```bash
(user@host)-$ singularity exec docker://reslp/iqtree:2.0.7 \
              iqtree \
              -s by_gene/trimmed/ \
              --prefix five_genes \
              -m MFP --seqtype AA -T 2 -bb 1000 
``` 

This will run for about 10 Minutes. You can check out the result `five_genes.treefile`, once it's done.

```bash
(user@host)-$ cat five_genes.treefile
```

__Congratulations, you've built your first phylogenomic tree!!!__

__5.) Automate the workflow with Snakemake__

A very neat way of handling this kind of thing is [Snakemake](https://snakemake.readthedocs.io/en/stable/).

The repository ships with a file called `Snakefile`. This file contains the instructions for running a basic workflow with Snakemake. Let's have a look.

```bash
(user@host)-$ less Snakefile #exit less with 'q'
```

In the Snakefile you'll see 'rules' (that's what individual steps in the analyses are called in the Snakemake world). Some of which should look familiar, because we just ran them manually, and then from within a simple bash script. Filenames etc. are replaced with variables but other than that..

Snakemake is installed on your system. In order run Snakemake you first need to enter a `conda` environment that we've set up. 

```bash
(user@host)-$ conda activate snakemake
(snakemake) (user@host)-$ snakemake -h
```

Now, let's try to do a Snakemake 'dry-run', providing a specific target file and see what happens. 

```bash
(user@host)-$ snakemake -n -rp auto/trimmed/193525at7742.clustalo.trimal.fasta
```


Now, you could extend the analyses to further genes.
```bash
(user@host)-$ snakemake -n -rp auto/trimmed/193525at7742.clustalo.trimal.fasta auto/trimmed/406935at7742.clustalo.trimal.fasta
```

Actually, running would happen if you remove the `-n` flag. 
```bash
(user@host)-$ snakemake -rp --use-singularity auto/trimmed/193525at7742.clustalo.trimal.fasta auto/trimmed/406935at7742.clustalo.trimal.fasta
```

Have fun playing around with this for a while ;-)

__6.) Full automation__


We are working on a pipeline for automating the entire process of phylogenomic analyses from BUSCO genes (for now). You can find it [here](https://github.com/reslp/phylociraptor).

The current repository is actually a snapshot of [phylociraptor](https://github.com/reslp/phylociraptor). In the base directory of this repository you could resume an analysis as shown below. If there is time we'll talk about the setup a little bit.

The main things you need are:
 - config file `data/config.vertebrata_minimal.yaml`
 - sample file `data/vertebrata_minimal.csv`

A few steps were already run for you - see the file `data/preparation.md`

```bash

#get table
./phylociraptor orthology -t serial=2 --config-file data/config.vertebrata_minimal.yaml

#filter-orthology
./phylociraptor filter-orthology -t serial=2 --config-file data/config.vertebrata_minimal.yaml --verbose

#align
./phylociraptor align -t serial=2 --config-file data/config.vertebrata_minimal.yaml --verbose

#filter align
./phylociraptor filter-align -t serial=2 --config-file data/config.vertebrata_minimal.yaml --verbose

#modeltest
./phylociraptor modeltest -t serial=2 --config-file data/config.vertebrata_minimal.yaml

#ml tree
./phylociraptor mltree -t serial=2 --config-file data/config.vertebrata_minimal.yaml --verbose

#speciestree
./phylociraptor speciestree -t serial=2 --config-file data/config.vertebrata_minimal.yaml --verbose

#figure
./phylociraptor report --config-file data/config.vertebrata_minimal.yaml 
./phylociraptor report --figure --config-file data/config.vertebrata_minimal.yaml

``` 
