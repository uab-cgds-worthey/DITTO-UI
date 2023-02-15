# DITTO-UI

Easy to use web interface for biologists to look for likely pathogenic variants and understand their deleteriousness using DITTO scores.

*!!! For research purposes only !!!*

## Description

A web app where anyone can lookup variants and understand the mechanism/details of
these variants such as domain, function, DITTO deleterious score and Clinvar reported significance.

## Data

We use dbNSFP data (downloaded on xx/xx/2022) for training DITTO and predictions. Domain information is extracted from Uniprot.

## Usage

DITTO can be accessed at this streamlit [site](https://cgds-ditto4nf.streamlit.app/).

### Installation

Installation simply requires fetching the source code. Following are required:

- Git

To fetch source code, change in to directory of your choice and run:

```sh
git clone \
    https://github.com/uab-cgds-worthey/DITTO-UI.git
```

### Requirements

*OS:*

Currently works only in Mac OS. Docker versions may need to be explored later to make it useable in Mac (and
potentially Windows).

*Tools:*

- Python 3.9
- Pip3

*Environment:*

We used conda environment to install the libraries and run the streamlit app, but one could use python virtual environment as well.

### Install required packages

Change in to root directory and run the commands below:

```sh
# create environment. Needed only the first time.
pip3 install -r requirements.txt
```

### Steps to run

#### Run Streamlit App

```sh
streamlit run src/Home.py
```

## Contact Info

Tarun Mamidi | tmamidi@uab.edu

