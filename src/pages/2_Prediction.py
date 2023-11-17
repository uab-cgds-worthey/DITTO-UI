import streamlit as st

import matplotlib.pyplot as plt
st.set_option(
    "deprecation.showPyplotGlobalUse", False
)  # To suppress MatplotlibDeprecationWarning to display SHAP plot
import pandas as pd
import yaml
import pickle
import json
from parse import OCApiParser
from predict import parse_and_predict
import shap
from tensorflow import keras
import numpy as np
from pathlib import Path

# Config the whole app
st.set_page_config(
    page_title="DITTO4NF",
    page_icon="🧊",
    layout="wide",  # initial_sidebar_state="expanded",
)


# Function to open and load config file for filtering columns and rows
# @st.cache_data
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


# Class to define colors for Clinvar classification
class ClinSigColors:
    default_colors = {
        "not seen in clinvar": "#969696",
        "other": "#969696",
        "not provided": "#969696",
        "Conflicting interpretations of pathogenicity": "#d8b365",
        "Benign": "#3182bd",
        "Likely benign": "#2166ac",
        "Benign/Likely benign": "#2166ac",
        "Uncertain significance": "#5ab4ac",
        "Uncertain significance, other": "#5ab4ac",
        "Pathogenic/Likely pathogenic": "#b2182b",
        "Likely pathogenic": "#d73027",
        "Pathogenic": "#b2182b",
    }


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")


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

def main():
    repo_root = Path(__file__).parent.parent.parent

    st.header(f"DITTO deleterious prediction with explanations")

    # Load the col config file as dictionary
    config_f = repo_root / "configs" / "col_config.yaml"
    config_dict = get_col_configs(config_f)

    # Load the data config file as dictionary
    data_config = repo_root / "configs" / "opencravat_test_config.json"
    parser = get_parser(data_config)

    # Load the model and data
    # df2, var, feature_names = load_lovd(config_dict)
    explainer, clf = load_model()

    st.subheader("Please input a variant of interest in build GRCh38:")

    col1, col2, col3, col4 = st.columns(4)
    chrom = col1.selectbox("Chromosome:", options=list(range(1, 22)) + ["X", "Y", "MT"])
    pos = col2.text_input("Position:", 2406483)
    ref = col3.text_input("Reference Nucleotide:", "C")
    alt = col4.text_input("Alternate Nucleotide:", "G")

    if st.button('Submit'):
        overall = parser.query_variant(
                chrom=str(chrom), pos=int(pos), ref=ref, alt=alt
            )

        st.subheader("**OpenCravat annotations**")
        st.dataframe(overall)

        st.write("\n\n")
        transcript = st.selectbox("Choose a transcript:", options=list(overall['transcript'].unique()))
        transcript_data = overall[overall['transcript'] == transcript].reset_index(drop=True)
        df2, y_score = parse_and_predict(transcript_data, config_dict, clf)

        # Download DITTO predictions
        st.download_button(
            label=f"Download annotations",
            data=convert_df(overall),
            file_name=f"OC_annotations.csv",
            mime="text/csv",
        )

        st.subheader("**DITTO prediction and explanations using SHAP**")

        pred_col1, pred_col2 = st.columns(2)

        # initialise data of lists to print on the webpage.
        var_scores = {
            "Source": [
                "DITTO score",
                "Clinvar Classification",
                "Clingen Classification",
                "gnomAD AF",
            ],
            "Values": [
                # str(round(1 - (ditto["DITTO"].values[0]), 2)),
                str(y_score[0][0]),
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


if __name__ == "__main__":
    main()
