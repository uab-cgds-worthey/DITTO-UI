# DITTO-UI

Easy to use web interface for biologists to look for genetic variants and understand their deleteriousness
using DITTO scores.

_!!! For research purposes only !!!_

## Description

A web app where anyone can lookup variants and understand the mechanism/details of these variants such as
function, DITTO deleterious score and Clinvar reported significance.

## Data

DITTO-UI comprises DITTO scores for any variant using annotations from openCravat
for making predictions. Annotations are extracted from openCravat API query on page render.

## Usage

DITTO-UI is deployed on the Streamlit Cloud: [DITTO-UI site](https://cgds-ditto.streamlit.app).

### Installation

Installation simply requires fetching the source code. Following are required:

- Git

To fetch source code, change in to directory of your choice and run:

```sh
    git clone https://github.com/uab-cgds-worthey/DITTO-UI.git
```

### Requirements

*OS:*

Currently works only in Mac OS. Docker versions may need to be explored later to make it useable in Mac (and
potentially Windows).

*Tools:*

- Python 3.11
- Pip3

*Environment:*

- [python virtual environment](https://docs.python.org/3/tutorial/venv.html)

### Install required packages

Change in to root directory and run the commands below:

```sh
# create environment. Needed only the first time.
pip3 install -r requirements.txt
```

### Run DITTO-UI locally

To run DITTO-UI locally make sure the environment has been succesfully made and then run the following commands

```sh
# run the DITTO-UI application using Streamlit
streamlit run src/Home.py
```

Once the application has started up it will open a new tab in your default browser to DITTO-UI

## Contact Info

Tarun Mamidi | tmamidi@uab.edu
