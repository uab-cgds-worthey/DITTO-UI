# DITTO-UI

Easy to use web interface for biologists to look for likely pathogenic variants and understand their deleteriousness
using DITTO scores.

_!!! For research purposes only !!!_

## Description

A web app where anyone can lookup variants and understand the mechanism/details of these variants such as
function, DITTO deleterious score and Clinvar reported significance.

## Data

DITTO-UI comprises precomputed DITTO scores for any variant using annotations from openCravat
for making predictions. Annotations are extracted from openCravat API query on page render.

## Usage

DITTO-UI is deployed on the Streamlit Cloud: [DITTO-UI site](https://cgds-ditto.streamlit.app).

### Local Installation and Setup

Installation simply requires fetching the source code. Following are required:

-   Git (version 2+)
-   Anaconda3 (a.k.a. Conda) or the drop-in replacement Mamba (a reimplementation of Conda, tested on version 0.25 and
    1.1.0, [install instructions](https://mamba.readthedocs.io/en/latest/installation.html))

To fetch source code, change in to directory of your choice and run:

```sh
git clone https://github.com/uab-cgds-worthey/DITTO-UI.git
```

#### Environement Creation

Change in to root directory and run the commands below:

```sh
# create environment with mamba
mamba env create -n ditto-env -f environment.yaml
# or
# create environment with conda
conda env create -n ditto-env -f environment.yaml
```

### Run DITTO-UI locally

To run DITTO-UI locally make sure the conda environment has been succesfully made and then run the following commands

```sh
# activate the DITTO-UI conda environment to deploy locally using Streamlit
# replace `mamba` with `conda` in the following command if using conda instead of mamba
mamba activate ditto-env

# run the DITTO-UI application using Streamlit
streamlit run src/Home.py
```

Once the application has started up it will open a new tab in your default browser to DITTO-UI

### Running DITTO in Streamlit Cloud

DITTO-UI is deployed on Streamlit Cloud using the same enviornment as used for local development, but there is only the
option to use `conda` for the deployment there. Changes to the environment need to be tested with `conda`s build process
to ensure that it'll be compatible with the Streamlit Cloud setup.

## Contact Info

Tarun Mamidi | tmamidi@uab.edu
