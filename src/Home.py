import streamlit as st

import matplotlib.pyplot as plt
st.set_option(
    "deprecation.showPyplotGlobalUse", False
)  # To suppress MatplotlibDeprecationWarning to display SHAP plot
import pandas as pd
import yaml
import pickle
import json
from utils.parse import OCApiParser
from utils.predict import parse_and_predict
import shap
from tensorflow import keras
import numpy as np
from pathlib import Path
import requests

# Config the whole app
st.set_page_config(
    page_title="DITTO",
    page_icon="🧊",
    layout="wide", initial_sidebar_state="expanded",
)


# Function to open and load config file for filtering columns and rows
@st.cache_data
def get_col_configs(config_f):
    with open(config_f) as fh:
        config_dict = yaml.safe_load(fh)

    # print(config_dict)
    return config_dict

# Function to open and load data config file for parsing opencravat output
@st.cache_data
def get_parser(data_config):
    with data_config.open("rt") as dc_fp:
        data_config_dict = json.load(dc_fp)

    parser = OCApiParser(data_config_dict)
    return parser

# Function to load model and weights
@st.cache_resource
def load_model():
    # Load background data to generate SHAP explainer object
    pkl_file = open(
        "./results/background.pkl",
        "rb",
    )
    background = pickle.load(pkl_file)
    pkl_file.close()

    # Load model and weights
    clf = keras.models.load_model("./results/Neural_network")
    clf.load_weights("./results/weights.h5")

    # Generate SHAP explainer object
    explainer = shap.KernelExplainer(clf.predict, background)
    return explainer, clf

# Function to query variant reference allele based on posiiton from UCSC API
@st.cache_data
def query_variant(chrom: str, pos: int, allele_len: int) -> json:
        if not chrom.startswith("chr"):
            chrom = "chr" + chrom
        url = (
            f"https://api.genome.ucsc.edu/getData/sequence?genome=hg38;chrom={chrom};start={pos};end={pos+allele_len}"
        )

        get_fields = requests.get(url, timeout=20)
        try:
            get_fields.raise_for_status()
        except requests.exceptions.RequestException as expt:
            print(
                f"Could not get UCSC Annotations for chrom={chrom} pos={str(pos)}"
            )
            raise expt

        return get_fields.json()

def main():
    repo_root = Path(__file__).parent.parent
    st.markdown("# DITTO")
    st.markdown("\n")
    head_col1, head_col2 = st.columns(2)
    head_col1.markdown(
        "### A tool for exploring genetic variants and their predicted functional impact."
    )
    head_col1.markdown("- DITTO (inspired by pokemon) is a tool for exploring any type of genetic variant and their predicted functional impact on transcript(s).")
    head_col1.markdown("- DITTO uses an explainable neural network model to predict the functional impact of variants and utilizes SHAP to explain the model's predictions.")
    head_col1.markdown("- DITTO provides annotations from OpenCravat, a tool for annotating variants with information from multiple data sources.")
    head_col1.markdown("- DITTO is currently trained on variants from ClinVar and is not intended for clinical use.")
    head_col1.markdown("- DITTO is a work in progress and we welcome your feedback and suggestions.")

    head_col2.markdown("![Alt Text](https://media.giphy.com/media/pMFmBkBTsDMOY/giphy.gif)")

    head_col1.markdown("\n\n")
    head_col1.markdown(
        "**Created by [Tarun Mamidi](https://www.linkedin.com/in/tkmamidi/) and"
        " [Liz Worthey](https://www.linkedin.com/in/lizworthey/)**"
        )

    # Load the col config file as dictionary
    config_f = repo_root / "configs" / "col_config.yaml"
    config_dict = get_col_configs(config_f)

    # Load the data config file as dictionary
    data_config = repo_root / "configs" / "opencravat_test_config.json"
    parser = get_parser(data_config)

    # Load the model and data
    # df2, var, feature_names = load_lovd(config_dict)
    explainer, clf = load_model()

    st.markdown("### Please input a variant of interest in build GRCh38:")
    st.markdown("**Note:** Please use the correct variant info for the build. You can check the correct variant info at [Ensembl](https://www.ensembl.org/index.html) or [UCSC](https://genome.ucsc.edu/index.html).")


    # Variant input
    col1, col2, col3, col4 = st.columns(4)
    chrom = col1.selectbox("Chromosome:", options=list(range(1, 22)) + ["X", "Y", "MT"])
    pos = col2.text_input("Position:", 2406483)
    ref = col3.text_input("Reference Nucleotide:", "C")
    actual_ref = query_variant(str(chrom), int(pos), len(ref))['dna']
    alt = col4.text_input("Alternate Nucleotide:", "G")

    if ref != actual_ref:
        st.warning(f"Provided reference nucleotide '{ref}' does not match the actual nucleotide '{actual_ref}' from reference genome. Please fix the variant info and try again.")
    else:
        st.success("Reference nucleotide matches the reference genome.")

        if st.button('Submit'):

            # Query variant annotations via opencravat API and get data as dataframe
            overall = parser.query_variant(
                    chrom=str(chrom), pos=int(pos), ref=ref, alt=alt
                )

            st.write("\n\n")

            # Select transcript
            transcript = st.selectbox("**Choose a transcript:**", options=list(overall['transcript'].unique()))

            # Filter data based on selected transcript
            transcript_data = overall[overall['transcript'] == transcript].reset_index(drop=True)

            # Parse and predict
            df2, y_score = parse_and_predict(transcript_data, config_dict, clf)

            st.subheader("**DITTO prediction and explanations using SHAP**")
            st.markdown("**Note:** DITTO score is the probability of a variant being deleterious. The higher the score (close to 1), the more likely the variant is deleterious.")

            pred_col1, pred_col2 = st.columns(2)

            # initialise data of lists to print on the webpage.
            var_scores = {
                "Source": [
                    "DITTO score",
                    "CADD score",
                    "SpliceAI score",
                    "Consequence",
                    "Clinvar Classification",
                    "Clingen Classification",
                    "gnomAD AF",
                ],
                "Values": [
                    # str(round(1 - (ditto["DITTO"].values[0]), 2)),
                    str(y_score[0][0]),
                    str(transcript_data["cadd.phred"].values[0]),
                    str(transcript_data[['spliceai.ds_ag','spliceai.ds_al','spliceai.ds_dg','spliceai.ds_dl']].max(axis=1).values[0]),
                    transcript_data["consequence"].values[0],
                    transcript_data["clinvar.sig"].values[0],
                    transcript_data["clingen.classification"].values[0],
                    transcript_data["gnomad3.af"].values[0],
                ],
            }
            # Create DataFrame
            pred_col1.dataframe(pd.DataFrame(var_scores))

            # SHAP explanation
            shap_value = explainer.shap_values(df2.values)[0]

            # SHAP explanation plot for a variant
            pred_col2.pyplot(
                shap.plots._waterfall.waterfall_legacy(
                    1 - explainer.expected_value[0],  # DITTO prediction for deleterious is (1 - y_pred)
                    np.negative(shap_value[0]),  # SHAP value for deleterious is negative
                    df2.values[0],
                    df2.columns,
                    max_display=20,
                )
            )

            st.subheader("**OpenCravat annotations**")
            st.dataframe(overall)

    st.markdown("---")

    left_info_col, right_info_col = st.columns(2)
    left_info_col.markdown(
        f"""
        ### Authors
        Please feel free to contact us with any issues, comments, or questions on our [GitHub page](https://github.com/uab-cgds-worthey/DITTO-UI).""",
    )
    left_info_col.markdown(
        f"""
        ##### Tarun Mamidi [![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/bukotsunikki.svg?style=social&label=Follow%20%40TarunMamidi7)](https://twitter.com/TarunMamidi7)
        - Email:  <tmamidi@uab.edu> or <mtkk94@gmail.com>
        - GitHub: https://github.com/tkmamidi
        ##### Dr. Liz Worthey [![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/bukotsunikki.svg?style=social&label=Follow%20%40lizworthey)](https://twitter.com/lizworthey)
        - Email: <lworthey@uab.edu>
        - GitHub: https://github.com/uab-cgds-worthey
        """,
    )
    right_info_col.markdown(
        """
            ### Funding
            - NIH
            - CGDS Lab Funds
             """
    )
    right_info_col.markdown(
        """
            ### License
            GNU General Public License v3.0
            """
    )

    st.markdown("---")
    st.markdown("Developed and Maintained by [Tarun Mamidi](https://www.linkedin.com/in/tkmamidi/)")
    st.markdown("[Center for Computational Genomics and Data Science](https://sites.uab.edu/cgds/)")
    # st.markdown(f"Most Recently Deposited Entry 09/28/2022")
    st.markdown("Copyright (c) 2023 CGDS")



if __name__ == "__main__":
    main()
