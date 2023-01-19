
Snakemake can be installed easily through conda.

The below instructions have been tested with conda installed through Miniconda (Miniconda3-py38_4.12.0).

First, create a config file for your environment. Use your favourite text editor to open a textfile called `snakemake_config.yaml`, and enter the following:

```bash
name: snakemake
channels:
  - conda-forge
  - bioconda
dependencies:
  - snakemake==5.9.1
```

This specifies that we want to call the environment 'snakemake', then we tell conda to look for dependencies in two channels, and we specifity that we want to install a specific Snakemake version. Save the file.

Then create the environment with conda.
```bash
(user@host)-$ conda env create -f snakemake_config.yaml 
```

Conda should run for about 10-15 Minutes and hopefully get Snakemake and all dependencies set up for you.

Don't forget to enter the environment before starting to play with Snakemake.
```bash
(user@host)-$ conda activate snakemake
```


