# DITTO-UI

Easy to use web interface for biologists to look for likely pathogenic variants and understand their deleteriousness
using DITTO scores.

_!!! For research purposes only !!!_

## Description

A web app where anyone can lookup variants and understand the mechanism/details of these variants such as domain,
function, DITTO deleterious score and Clinvar reported significance.

## Data

We use dbNSFP data (downloaded on xx/xx/2022) for training DITTO and predictions. Domain information is extracted from
Uniprot.

## Usage

DITTO-UI is deployed on the Streamlit Cloud: [DITTO-UI site](https://cgds-ditto4nf.streamlit.app/).

### Local Installation and Setup

Installation simply requires fetching the source code. Following are required:

-   Git (version 2+)
-   Mamba (tested on version 0.25 and 1.1.0,
    [install instructions](https://mamba.readthedocs.io/en/latest/installation.html))

To fetch source code, change in to directory of your choice and run:

```sh
git clone https://github.com/uab-cgds-worthey/DITTO-UI.git
```

#### Environement Creation

Change in to root directory and run the commands below:

```sh
# create environment
mamba env create -n ditto-env -f environment.yml
```

**NOTE**: Please make sure you have
[strict channel priority](https://conda-forge.org/docs/user/tipsandtricks.html#how-to-fix-it) turned off to create the
enviroment as having it enabled will not allow the install of Pandas and cause the build to fail.

### Run DITTO-UI locally

To run DITTO-UI locally make sure the conda environment has been succesfully made and then run the following commands

```sh
# activate the DITTO-UI conda environment to deploy locally using Streamlit
mamba activate ditto-env

# run the DITTO-UI application using Streamlit
streamlit run src/ui_ditto.py
```

Once the application has started up it will open a new tab in your default browser to DITTO-UI

## Contact Info

Tarun Mamidi | tmamidi@uab.edu
